#include "libfinance/client.hpp"

#include <cerrno>
#include <cstdlib>
#include <iostream>
#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>

#include <unistd.h>

#include <arrow/api.h>
#include <arrow/io/memory.h>
#include <arrow/ipc/reader.h>

#include "internal.hpp"
#include "wire.hpp"

namespace libfinance {

namespace {

// ---------------------------------------------------------------- the process-wide client

std::mutex client_lock;
std::unique_ptr<RpcClient> client;

std::mutex warning_lock;
std::function<void(const std::string&)> warning_handler = [](const std::string& message) {
  std::cerr << "libfinance warning: " << message << "\n";
};

std::mutex caches_lock;
std::vector<std::function<void()>> caches;

// ---------------------------------------------------------------- pandas orient=table JSON

//: The column type of a pandas schema field. An object column (e.g. of Decimals) is declared
//: "string" while its values are numbers, and pandas reads them back as numbers: such a column is
//: typed by what its values are.
std::shared_ptr<arrow::DataType> arrow_type(const std::string& pandas_type, const Json& rows, const std::string& name) {
  if (pandas_type == "integer") return arrow::int64();
  if (pandas_type == "number") return arrow::float64();
  if (pandas_type == "boolean") return arrow::boolean();
  if (pandas_type == "datetime") return arrow::timestamp(arrow::TimeUnit::MILLI);
  bool numbers = true, integers = true, booleans = true, any = false;
  for (const Json& row : rows) {
    auto found = row.find(name);
    if (found == row.end() || found->is_null()) continue;
    any = true;
    numbers = numbers && found->is_number();
    integers = integers && found->is_number_integer();
    booleans = booleans && found->is_boolean();
  }
  if (any && integers) return arrow::int64();
  if (any && numbers) return arrow::float64();
  if (any && booleans) return arrow::boolean();
  return arrow::utf8();
}

//: "2024-01-02T09:30:00.000[Z|+08:00]" -> milliseconds since the epoch (the zone is ignored).
int64_t epoch_millis(const std::string& text) {
  const int64_t days = DateLike(text.substr(0, 10)).date().days_since_epoch();
  int hour = 0, minute = 0, second = 0, millis = 0;
  if (text.size() > 11) std::sscanf(text.c_str() + 11, "%d:%d:%d.%d", &hour, &minute, &second, &millis);
  return ((days * 24 + hour) * 60 + minute) * 60000LL + second * 1000LL + millis;
}

void check(const arrow::Status& status) {
  if (!status.ok()) throw std::invalid_argument("libfinance: " + status.ToString());
}

std::shared_ptr<arrow::Array> column_of(const Json& rows, const std::string& name,
                                        const std::shared_ptr<arrow::DataType>& type) {
  std::unique_ptr<arrow::ArrayBuilder> builder;
  check(arrow::MakeBuilder(arrow::default_memory_pool(), type, &builder));
  for (const Json& row : rows) {
    auto found = row.find(name);
    if (found == row.end() || found->is_null()) {
      check(builder->AppendNull());
      continue;
    }
    const Json& value = *found;
    switch (type->id()) {
      case arrow::Type::INT64:
        check(static_cast<arrow::Int64Builder&>(*builder).Append(value.get<int64_t>()));
        break;
      case arrow::Type::DOUBLE:
        check(static_cast<arrow::DoubleBuilder&>(*builder).Append(value.get<double>()));
        break;
      case arrow::Type::BOOL:
        check(static_cast<arrow::BooleanBuilder&>(*builder).Append(value.get<bool>()));
        break;
      case arrow::Type::TIMESTAMP:
        check(static_cast<arrow::TimestampBuilder&>(*builder).Append(epoch_millis(value.get<std::string>())));
        break;
      default:
        check(static_cast<arrow::StringBuilder&>(*builder).Append(value.is_string() ? value.get<std::string>()
                                                                                      : value.dump()));
    }
  }
  std::shared_ptr<arrow::Array> array;
  check(builder->Finish(&array));
  return array;
}

//: pandas' DataFrame.to_json(orient="table"). The default RangeIndex (primaryKey ["index"]) is
//: dropped; a named index becomes ordinary columns, as reset_index() would make it.
Table from_pandas_json(const std::string& text) {
  const Json document = Json::parse(text);
  const Json& fields = document.at("schema").at("fields");
  const Json primary = document.at("schema").value("primaryKey", Json::array());
  const Json& rows = document.at("data");
  arrow::FieldVector schema;
  arrow::ArrayVector columns;
  for (const Json& field : fields) {
    const std::string name = field.at("name").get<std::string>();
    if (name == "index" && primary == Json::array({"index"})) continue;
    const auto type = arrow_type(field.value("type", "string"), rows, name);
    schema.push_back(arrow::field(name, type));
    columns.push_back(column_of(rows, name, type));
  }
  return arrow::Table::Make(arrow::schema(schema), columns, static_cast<int64_t>(rows.size()));
}

Table from_arrow_ipc(const Json::binary_t& bytes) {
  auto buffer = std::make_shared<arrow::Buffer>(bytes.data(), static_cast<int64_t>(bytes.size()));
  auto reader = arrow::ipc::RecordBatchStreamReader::Open(std::make_shared<arrow::io::BufferReader>(buffer));
  if (!reader.ok()) throw std::invalid_argument("libfinance: " + reader.status().ToString());
  auto table = (*reader)->ToTable();
  if (!table.ok()) throw std::invalid_argument("libfinance: " + table.status().ToString());
  // the buffer borrows `bytes`; copy out so the table outlives the answer
  auto owned = (*table)->CombineChunks();
  if (!owned.ok()) throw std::invalid_argument("libfinance: " + owned.status().ToString());
  return *owned;
}

}  // namespace

// ---------------------------------------------------------------- RpcClient

// 一个 wire::Connection 一次只能有一个请求在途（同步收发、不按 request_id 分发）。原先 RpcClient 只有一条
// 连接，多线程共用时所有请求排队：8 个并发 200 ms 的请求要 1.6 s，跨公网时整个进程的吞吐被钉在 1/RTT。
// 现在是一个连接池：每个请求借一条空闲连接，没有空闲的就新开（最多 max_connections 条），用完归还。
// 协议、服务端都不用改；单线程调用者仍只有一条连接。

struct RpcClient::Connection {
  struct Lent {
    std::unique_ptr<wire::Connection> wire;
    int generation = -1;  // 已以第几次 login() 的账号登录；-1 为匿名
  };
  struct Pool {
    std::mutex lock;
    std::condition_variable returned;
    std::vector<Lent> idle;
    int open = 0;
  };

  Connection(std::string host_, int port_, int timeout_, int max_)
      : host(std::move(host_)), port(port_), timeout(timeout_), max_open(std::max(1, max_)), pool(new Pool), pid(::getpid()) {}

  ~Connection() {
    // fork 之后被替换掉的旧池子故意不删（见 current_pool），这里只删本进程的
    if (pid.load() == ::getpid()) delete pool.load();
  }

  //: 本进程的池子。fork 后子进程第一次用到时换一个新池子：父进程的连接（及其可能正被父进程某个线程
  //: 持有的锁）留给父进程，旧池子不析构——析构会关掉、甚至等待那些锁。
  Pool& current_pool() {
    const pid_t me = ::getpid();
    if (pid.load() != me) {
      pool.store(new Pool);
      pid.store(me);
    }
    return *pool.load();
  }

  Lent acquire() {
    Pool& p = current_pool();
    Lent lent;
    {
      std::unique_lock<std::mutex> guard(p.lock);
      p.returned.wait(guard, [&] { return !p.idle.empty() || p.open < max_open; });
      if (!p.idle.empty()) {
        lent = std::move(p.idle.back());
        p.idle.pop_back();
      } else {
        ++p.open;
      }
    }
    if (!lent.wire) {
      try {
        lent.wire = std::make_unique<wire::Connection>(host, port, timeout);
      } catch (...) {
        std::lock_guard<std::mutex> guard(p.lock);
        --p.open;
        p.returned.notify_one();
        throw;
      }
    }
    // login() 之后借出的连接：先以该账号登录（服务端把等级记在连接上）
    std::pair<int, Json> account;
    {
      std::lock_guard<std::mutex> guard(login_lock);
      account = {generation, credentials};
    }
    if (lent.generation != account.first && !account.second.is_null()) {
      try {
        lent.wire->login(account.second);
      } catch (...) {
        give_back(std::move(lent));
        throw;
      }
      lent.generation = account.first;
    }
    return lent;
  }

  void give_back(Lent lent) {
    Pool& p = current_pool();
    std::lock_guard<std::mutex> guard(p.lock);
    p.idle.push_back(std::move(lent));
    p.returned.notify_one();
  }

  //: 借一条连接、用完自动归还（异常时也归还：wire::Connection 遇到传输错误会自行关闭、下次重开）
  class Lease {
   public:
    explicit Lease(Connection& owner) : owner_(owner), lent_(owner.acquire()) {}
    ~Lease() { owner_.give_back(std::move(lent_)); }
    wire::Connection* operator->() { return lent_.wire.get(); }
    Lent& lent() { return lent_; }

   private:
    Connection& owner_;
    Lent lent_;
  };

  const std::string host;
  const int port;
  const int timeout;
  const int max_open;
  std::atomic<Pool*> pool;
  std::atomic<pid_t> pid;

  std::mutex login_lock;
  Json credentials;   // null until login() succeeds
  int generation = 0;
};

RpcClient::RpcClient(const std::string& host, int port, int timeout_seconds, int max_connections)
    : connection_(std::make_unique<Connection>(host, port, timeout_seconds, max_connections)) {
  Connection::Lease first(*connection_);  // 构造时就连：连不上的服务端在这里报错（与原先一致）
}

RpcClient::~RpcClient() = default;

Json RpcClient::call(const std::string& function, const Json& args) const {
  constexpr int kAttempts = 3;
  for (int attempt = 1;; ++attempt) {
    try {
      Connection::Lease lease(*connection_);
      return lease->call(function, args);
    } catch (const wire::TransportError& error) {
      // 超时不重试：服务端仍在执行这个请求，重发只会让同一个重查询再跑一遍（最坏 3 × 300 s）
      if (error.code() == wire::kTimeout || attempt == kAttempts) throw;
      // 连接、协议错误：请求可能没到服务端，在新连接上再试
      std::this_thread::sleep_for(std::chrono::milliseconds(600));
    }
  }
}

Json RpcClient::login(const std::string& username, const std::string& password) {
  const Json args{{"username", username}, {"password", password}};
  Connection::Lease lease(*connection_);
  Json answer = lease->login(args);   // 账号不对时抛 LoginError，已保存的账号不变
  std::lock_guard<std::mutex> guard(connection_->login_lock);
  connection_->credentials = args;
  lease.lent().generation = ++connection_->generation;  // 其余连接在下次借出时登录
  return answer;
}

Json login(const std::string& username, const std::string& password) {
  return get_client().login(username, password);
}

std::string default_host() {
  const char* host = std::getenv("LIBFINANCE_HOST");
  return host != nullptr && *host != '\0' ? host : "libfinance.tech";
}

int default_port() {
  const char* port = std::getenv("LIBFINANCE_PORT");
  if (port == nullptr || *port == '\0') return 8080;
  // std::atoi("abc") 是 0、atoi("8080x") 是 8080：一个写错的变量会变成连不上 port 0，报的错与真正原因无关
  char* end = nullptr;
  errno = 0;
  const long value = std::strtol(port, &end, 10);
  if (errno != 0 || end == port || *end != '\0' || value < 1 || value > 65535)
    throw std::invalid_argument(std::string("LIBFINANCE_PORT: a port number 1..65535 expected, got '") + port + "'");
  return static_cast<int>(value);
}

void init_client(const std::string& host, int port, int timeout_seconds, int max_connections) {
  std::lock_guard<std::mutex> guard(client_lock);
  if (!client) client = std::make_unique<RpcClient>(host, port, timeout_seconds, max_connections);
}

RpcClient& get_client() {
  {
    std::lock_guard<std::mutex> guard(client_lock);
    if (client) return *client;
  }
  try {
    init_client();
  } catch (const RpcError& error) {
    throw RpcError(error.code(), "client auto-connect to " + default_host() + ":" + std::to_string(default_port()) +
                                     " failed: " + error.message() +
                                     ". Call init_client(host, port) before using the libfinance functions");
  }
  return *client;
}

Table as_table(const Json& answer) {
  if (answer.is_object()) {
    const std::string type = answer.value("type", "");
    if (type == "arrow" && answer.contains("data") && answer["data"].is_binary())
      return from_arrow_ipc(answer["data"].get_binary());
    if (type == "pandas" && answer.contains("data") && answer["data"].is_string())
      return from_pandas_json(answer["data"].get<std::string>());
  }
  if (answer.is_null()) return nullptr;
  throw std::invalid_argument("libfinance: not a table answer: " + answer.dump().substr(0, 200));
}

void set_warning_handler(std::function<void(const std::string&)> handler) {
  std::lock_guard<std::mutex> guard(warning_lock);
  warning_handler = std::move(handler);
}

void clear_cache() {
  std::lock_guard<std::mutex> guard(caches_lock);
  for (const auto& clear : caches) clear();
}

// ---------------------------------------------------------------- detail

namespace detail {

Json call(const std::string& function, const Json& args) { return get_client().call(function, args); }

Table call_table(const std::string& function, const Json& args) { return as_table(call(function, args)); }

void warn(const std::string& message) {
  std::lock_guard<std::mutex> guard(warning_lock);
  if (warning_handler) warning_handler(message);
}

void register_cache(std::function<void()> clear) {
  std::lock_guard<std::mutex> guard(caches_lock);
  caches.push_back(std::move(clear));
}

namespace {

std::optional<std::string> ask_data_version() {
  try {  // a cache must never make a query fail: without a version it falls back to a TTL
    const Json pong = call("ping", Json::object());
    if (pong.is_object() && pong.contains("data_version") && pong["data_version"].is_string())
      return pong["data_version"].get<std::string>();
  } catch (const std::exception&) {
  }
  return std::nullopt;
}

struct VersionState {
  std::mutex lock;
  std::mutex asking;  // 没有版本时只让一个线程同步去问，其余等它的答案
  std::optional<std::string> version;
  std::chrono::steady_clock::time_point checked_at;
  bool checked = false;
  bool refreshing = false;
};

VersionState& version_state() {
  // 不析构：后台刷新线程可能比 main 活得久。fork 后换一份：父进程的刷新线程不在子进程里，
  // 它的 refreshing 标记永远不会清掉，持有的锁也永远不会释放。
  static std::atomic<VersionState*> state{new VersionState};
  static std::atomic<pid_t> owner{::getpid()};
  if (owner.load() != ::getpid()) {
    state.store(new VersionState);
    owner.store(::getpid());
  }
  return *state.load();
}

}  // namespace

//: Python 的 stale-while-revalidate：2 秒内直接复用；过期但已知一个版本时，先用它答这次调用、
//: 在后台再问（原先每次过期都同步 ping，交互式使用里几乎每个调用多付一个往返）；
//: 还不知道任何版本时才同步问，并发的同步询问合并成一次。
std::optional<std::string> current_data_version() {
  VersionState& state = version_state();
  const auto now = std::chrono::steady_clock::now();
  std::chrono::steady_clock::time_point asked_at;
  {
    std::lock_guard<std::mutex> guard(state.lock);
    if (state.checked && now - state.checked_at < std::chrono::seconds(2)) return state.version;
    if (state.checked && state.version) {
      if (!state.refreshing) {
        state.refreshing = true;
        std::thread([&state] {
          const auto value = ask_data_version();
          std::lock_guard<std::mutex> guard(state.lock);
          state.version = value;
          state.checked_at = std::chrono::steady_clock::now();
          state.refreshing = false;
        }).detach();
      }
      return state.version;
    }
    asked_at = state.checked_at;
  }
  std::lock_guard<std::mutex> asking(state.asking);
  {
    std::lock_guard<std::mutex> guard(state.lock);
    if (state.checked && state.checked_at != asked_at &&
        std::chrono::steady_clock::now() - state.checked_at < std::chrono::seconds(2))
      return state.version;
  }
  const auto value = ask_data_version();
  std::lock_guard<std::mutex> guard(state.lock);
  state.version = value;
  state.checked_at = std::chrono::steady_clock::now();
  state.checked = true;
  return state.version;
}

}  // namespace detail

}  // namespace libfinance
