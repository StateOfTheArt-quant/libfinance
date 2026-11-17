// A large get_price is split by code across the client's connections (PERF-03), offline against a
// loopback server. Each TCP connection over a cross-border path is fast for its first megabytes and then
// throttled to 50-80 KB/s (measured 2026-11-17); the parts run on the RpcClient's connection pool and the
// merged panel is the same as one query's.
#include <gtest/gtest.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstdlib>
#include <cstring>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <vector>

#include <arrow/api.h>
#include <arrow/io/memory.h>
#include <arrow/ipc/writer.h>
#include <lz4frame.h>

#include <libfinance/client.hpp>
#include <libfinance/errors.hpp>
#include <libfinance/price.hpp>

namespace lf = libfinance;
using Json = lf::Json;

namespace {

bool read_exact(int fd, char* out, size_t size) {
  for (size_t got = 0; got < size;) {
    const ssize_t n = ::recv(fd, out + got, size - got, 0);
    if (n <= 0) return false;
    got += static_cast<size_t>(n);
  }
  return true;
}

std::string lz4_decompress(const std::string& in) {
  LZ4F_dctx* context = nullptr;
  LZ4F_createDecompressionContext(&context, LZ4F_VERSION);
  std::string out;
  std::vector<char> buffer(1 << 16);
  size_t offset = 0;
  while (offset < in.size()) {
    size_t produced = buffer.size(), consumed = in.size() - offset;
    LZ4F_decompress(context, buffer.data(), &produced, in.data() + offset, &consumed, nullptr);
    out.append(buffer.data(), produced);
    offset += consumed;
    if (consumed == 0 && produced == 0) break;
  }
  LZ4F_freeDecompressionContext(context);
  return out;
}

int32_t days_of(const std::string& iso) { return lf::DateLike(iso).date().days_since_epoch(); }

//: daybar's flat table: one row per code and weekday, close = row number within the code.
Json bars_answer(const std::vector<std::string>& codes, const std::string& start, const std::string& end) {
  arrow::StringBuilder ids;
  arrow::Date32Builder dates;
  arrow::DoubleBuilder closes;
  for (const auto& code : codes) {
    double close = 0;
    for (int32_t day = days_of(start); day <= days_of(end); ++day) {
      if (((day % 7 + 7) % 7 + 3) % 7 >= 5) continue;
      (void)ids.Append(code);
      (void)dates.Append(day);
      (void)closes.Append(close++);
    }
  }
  const auto table = arrow::Table::Make(
      arrow::schema({arrow::field("order_book_id", arrow::utf8()), arrow::field("session_date", arrow::date32()),
                     arrow::field("close", arrow::float64())}),
      {ids.Finish().ValueOrDie(), dates.Finish().ValueOrDie(), closes.Finish().ValueOrDie()});
  auto sink = arrow::io::BufferOutputStream::Create().ValueOrDie();
  auto writer = arrow::ipc::MakeStreamWriter(sink, table->schema()).ValueOrDie();
  (void)writer->WriteTable(*table);
  (void)writer->Close();
  const auto buffer = sink->Finish().ValueOrDie();
  return {{"type", "arrow"}, {"data", Json::binary(std::vector<uint8_t>(buffer->data(), buffer->data() + buffer->size()))}};
}

//: Answers get_price on every connection; a code containing "BAD" is refused. Records each request's
//: connection and codes.
class BarsServer {
 public:
  BarsServer() {
    listener_ = ::socket(AF_INET, SOCK_STREAM, 0);
    const int on = 1;
    setsockopt(listener_, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    ::bind(listener_, reinterpret_cast<sockaddr*>(&address), sizeof(address));
    socklen_t length = sizeof(address);
    getsockname(listener_, reinterpret_cast<sockaddr*>(&address), &length);
    port_ = ntohs(address.sin_port);
    ::listen(listener_, 16);
    std::thread([this] { accept_loop(); }).detach();
  }
  int port() const { return port_; }

  struct Request {
    int connection;
    std::vector<std::string> codes;
  };
  std::vector<Request> take_requests() {
    std::lock_guard<std::mutex> guard(lock_);
    std::vector<Request> out;
    out.swap(requests_);
    return out;
  }

 private:
  void accept_loop() {
    for (int connection = 1;; ++connection) {
      const int fd = ::accept(listener_, nullptr, nullptr);
      if (fd < 0) return;
      std::thread([this, fd, connection] { serve(fd, connection); }).detach();
    }
  }

  void serve(int fd, int connection) {
    for (;;) {
      char header[4];
      if (!read_exact(fd, header, 4)) break;
      const uint32_t body = ntohl(*reinterpret_cast<uint32_t*>(header));
      std::string data(body, '\0');
      if (!read_exact(fd, data.data(), body)) break;
      if (data[0] != 0x01) continue;  // PONGs
      const uint32_t request_id = ntohl(*reinterpret_cast<const uint32_t*>(data.data() + 1));
      const std::string payload = data.substr(6);
      const Json request =
          Json::from_msgpack(static_cast<uint8_t>(data[5]) & 0x01 ? lz4_decompress(payload) : payload);
      Json envelope;
      if (request.at("function") == "get_price") {
        const Json& args = request.at("args");
        const auto codes = args.at("order_book_ids").get<std::vector<std::string>>();
        {
          std::lock_guard<std::mutex> guard(lock_);
          requests_.push_back({connection, codes});
        }
        bool refused = false;
        for (const auto& code : codes) refused = refused || code.find("BAD") != std::string::npos;
        if (refused)
          envelope = {{"status", "error"}, {"code", 2001}, {"message", "unknown order_book_id"}, {"kind", "ValueError"}};
        else
          envelope = {{"status", "ok"}, {"code", 0},
                      {"result", bars_answer(codes, args.at("start_date"), args.at("end_date"))}};
      } else {
        envelope = {{"status", "ok"}, {"code", 0}, {"result", Json()}};
      }
      const std::vector<uint8_t> packed = Json::to_msgpack(envelope);
      std::string frame(4, '\0');
      const uint32_t length = htonl(static_cast<uint32_t>(6 + packed.size()));
      std::memcpy(frame.data(), &length, 4);
      frame.push_back(0x02);
      const uint32_t id = htonl(request_id);
      frame.append(reinterpret_cast<const char*>(&id), 4);
      frame.push_back(0x00);
      frame.append(packed.begin(), packed.end());
      ::send(fd, frame.data(), frame.size(), MSG_NOSIGNAL);
    }
    ::close(fd);
  }

  int listener_ = -1;
  int port_ = 0;
  std::mutex lock_;
  std::vector<Request> requests_;
};

BarsServer& server() {
  static BarsServer* instance = [] {
    auto* created = new BarsServer();  // outlives the process-wide client
    lf::init_client("127.0.0.1", created->port(), 60, 8);
    return created;
  }();
  return *instance;
}

std::vector<std::string> codes(int count) {
  std::vector<std::string> out;
  for (int i = 0; i < count; ++i) {
    char code[16];
    std::snprintf(code, sizeof(code), "%06d.XSHE", i + 1);
    out.emplace_back(code);
  }
  return out;
}

class Striped : public ::testing::Test {
 protected:
  void SetUp() override {
    server().take_requests();
    ::unsetenv("LIBFINANCE_PARALLEL");
  }
  void TearDown() override { ::unsetenv("LIBFINANCE_PARALLEL"); }
};

}  // namespace

// 100 codes x 262 weekdays of 2024 = 26 200 rows: three parts of at most 10 000 rows
TEST_F(Striped, ALargeQueryIsSplitByCodeAcrossConnections) {
  const auto ids = codes(100);
  const auto panel = lf::get_price(ids, "2024-01-01", "2024-12-31");
  const auto requests = server().take_requests();
  ASSERT_EQ(requests.size(), 3u);
  std::set<int> connections;
  std::vector<std::string> asked;
  for (const auto& request : requests) {
    connections.insert(request.connection);
    EXPECT_LE(request.codes.size(), 34u);
    asked.insert(asked.end(), request.codes.begin(), request.codes.end());
  }
  EXPECT_EQ(connections.size(), 3u);  // in parallel, each on its own connection
  EXPECT_EQ(std::set<std::string>(asked.begin(), asked.end()), std::set<std::string>(ids.begin(), ids.end()));
  EXPECT_EQ(asked.size(), ids.size());
  ASSERT_TRUE(panel);
  EXPECT_EQ(panel->num_rows(), 100 * 262);
}

TEST_F(Striped, TheMergedPanelIsTheOneQueryPanel) {
  const auto ids = codes(100);
  const auto split = lf::get_price(ids, "2024-01-01", "2024-12-31");
  ::setenv("LIBFINANCE_PARALLEL", "1", 1);
  const auto whole = lf::get_price(ids, "2024-01-01", "2024-12-31");
  const auto requests = server().take_requests();
  ASSERT_EQ(requests.size(), 4u);  // three parts, then the whole
  EXPECT_EQ(requests.back().codes.size(), 100u);
  ASSERT_TRUE(split && whole);
  ASSERT_TRUE(split->CombineChunks().ValueOrDie()->Equals(*whole->CombineChunks().ValueOrDie()));
}

TEST_F(Striped, ASmallQueryIsOneRequest) {
  lf::get_price(codes(30), "2024-01-01", "2024-12-31");  // 7 860 rows
  EXPECT_EQ(server().take_requests().size(), 1u);
}

TEST_F(Striped, PartsAreCappedByLibfinanceParallel) {
  ::setenv("LIBFINANCE_PARALLEL", "2", 1);
  lf::get_price(codes(300), "2024-01-01", "2024-12-31");  // 78 600 rows: 8 parts without the cap
  EXPECT_EQ(server().take_requests().size(), 2u);
}

TEST_F(Striped, ARefusedPartIsRaised) {
  auto ids = codes(100);
  ids[90] = "BAD.XSHE";
  try {
    lf::get_price(ids, "2024-01-01", "2024-12-31");
    FAIL() << "expected RpcError";
  } catch (const lf::RpcError& error) {
    EXPECT_EQ(error.code(), 2001);
  }
  EXPECT_EQ(server().take_requests().size(), 3u);  // every part ran; none was retried
}
