#include "libfinance/client.hpp"

#include <cstdlib>
#include <iostream>
#include <mutex>
#include <thread>

#include <arrow/api.h>
#include <arrow/io/memory.h>
#include <arrow/ipc/reader.h>
#include <contextrpc/client.h>

#include "internal.hpp"

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

struct RpcClient::Connection {
  contextrpc::Client rpc;
  Connection(const std::string& host, int port) : rpc(host, static_cast<uint16_t>(port)) {}
};

RpcClient::RpcClient(const std::string& host, int port) {
  try {
    connection_ = std::make_unique<Connection>(host, port);
  } catch (const contextrpc::RpcError& error) {
    throw RpcError(error.code(), error.what());
  }
}

RpcClient::~RpcClient() = default;

Json RpcClient::call(const std::string& function, const Json& args) const {
  constexpr int kAttempts = 3;
  for (int attempt = 1;; ++attempt) {
    try {
      return connection_->rpc.call(function, args);
    } catch (const contextrpc::RpcError& error) {
      const bool unreachable = error.code() < 0;  // CONNECTION_FAILED / TIMEOUT: worth another try
      if (!unreachable || attempt == kAttempts) {
        const Json& answer = error.response();
        const std::string message = answer.is_object() && answer.contains("message") && answer["message"].is_string()
                                        ? answer["message"].get<std::string>()
                                        : error.what();
        throw RpcError(error.code(), message,
                       answer.is_object() ? answer.value("kind", std::string()) : std::string());
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(600));
    }
  }
}

std::string default_host() {
  const char* host = std::getenv("LIBFINANCE_HOST");
  return host != nullptr && *host != '\0' ? host : "libfinance.tech";
}

int default_port() {
  const char* port = std::getenv("LIBFINANCE_PORT");
  return port != nullptr && *port != '\0' ? std::atoi(port) : 8080;
}

void init_client(const std::string& host, int port) {
  std::lock_guard<std::mutex> guard(client_lock);
  if (!client) client = std::make_unique<RpcClient>(host, port);
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

std::optional<std::string> current_data_version() {
  static std::mutex lock;
  static std::optional<std::string> version;
  static std::chrono::steady_clock::time_point checked_at;
  static bool checked = false;
  const auto now = std::chrono::steady_clock::now();
  {
    std::lock_guard<std::mutex> guard(lock);
    if (checked && now - checked_at < std::chrono::seconds(2)) return version;
  }
  std::optional<std::string> value;
  try {  // a cache must never make a query fail: without a version it falls back to a TTL
    const Json pong = call("ping", Json::object());
    if (pong.is_object() && pong.contains("data_version") && pong["data_version"].is_string())
      value = pong["data_version"].get<std::string>();
  } catch (const std::exception&) {
  }
  std::lock_guard<std::mutex> guard(lock);
  version = value;
  checked_at = std::chrono::steady_clock::now();
  checked = true;
  return version;
}

}  // namespace detail

}  // namespace libfinance
