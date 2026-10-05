// QuoteApi against a gateway on the loopback that speaks the protocol: login with the ticket given,
// one receipt per order_book_id subscribed, then quotes whose inst_seq skips one.
#include <gtest/gtest.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <libfinance/errors.hpp>
#include <libfinance/quote_api.hpp>

namespace lf = libfinance;
namespace qp = libfinance::quote_protocol;

namespace {

template <typename T>
void put(std::string& out, T value) {
  char raw[sizeof(T)];
  std::memcpy(raw, &value, sizeof(T));
  out.append(raw, sizeof(T));
}
void fixed(std::string& out, const std::string& text, size_t n) {
  out += text.substr(0, n - 1);
  out.append(n - std::min(text.size(), n - 1), '\0');
}
template <typename T>
T get(const std::string& data, size_t at) {
  T value;
  std::memcpy(&value, data.data() + at, sizeof(T));
  return value;
}
std::string cut(const std::string& data, size_t at, size_t n) {
  const std::string field = data.substr(at, n);
  return field.substr(0, field.find('\0'));
}

std::string login_rsp(int32_t error) {
  std::string body;
  put<int32_t>(body, error);
  fixed(body, error ? "bad ticket" : "ok", 64);
  put<uint64_t>(body, 1);       // session
  put<int64_t>(body, 4102444800000);
  put<int32_t>(body, 50);       // max subscriptions
  put<int32_t>(body, 2);
  put<int32_t>(body, 100);
  put<uint8_t>(body, 0);
  body.append(3, '\0');
  put<uint64_t>(body, 0x180);
  put<int64_t>(body, 1);        // epoch
  return body;
}

std::string sub_rsp(const std::string& request) {  // echoes the SubReq: source, exchange, code
  std::string body;
  fixed(body, cut(request, 0, 16).empty() ? "auto" : cut(request, 0, 16), 16);
  fixed(body, cut(request, 16, 16), 16);
  fixed(body, cut(request, 32, 32), 32);
  put<int32_t>(body, 0);
  fixed(body, "", 64);
  put<int32_t>(body, 1);
  put<int32_t>(body, 50);
  return body;
}

//: One quote record (envelope + 529-byte quote + padding) of 600519.XSHG with this inst_seq.
std::string quote_record(uint64_t seq, uint64_t inst_seq, double last) {
  std::string quote;
  put<int64_t>(quote, 1700000000000);
  fixed(quote, "600519", 32);
  fixed(quote, "XSHG", 16);
  put<int8_t>(quote, 1);
  for (int i = 0; i < 17; ++i) put<double>(quote, i == 2 ? last : 0.0);
  put<int64_t>(quote, 0);
  for (int i = 0; i < 40; ++i) put<double>(quote, 0.0);
  fixed(quote, "T", 8);
  std::string record;
  put<uint32_t>(record, 3);
  put<uint16_t>(record, 401);
  put<uint16_t>(record, static_cast<uint16_t>(quote.size()));
  put<uint32_t>(record, 0);
  put<uint32_t>(record, 0);
  put<uint64_t>(record, seq);
  put<uint64_t>(record, inst_seq);
  put<uint64_t>(record, lf::instrument_hash("XSHG", "600519"));
  put<int64_t>(record, 0);
  put<int64_t>(record, 0);
  record += quote;
  record.append(((record.size() + 7) & ~size_t(7)) - record.size(), '\0');
  return record;
}

class FakeGateway {
 public:
  FakeGateway() {
    listener_ = ::socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (::bind(listener_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0 || ::listen(listener_, 1) != 0)
      throw std::runtime_error("cannot listen");
    socklen_t size = sizeof(addr);
    ::getsockname(listener_, reinterpret_cast<sockaddr*>(&addr), &size);
    port_ = ntohs(addr.sin_port);
    thread_ = std::thread([this] { serve(); });
  }
  ~FakeGateway() {
    ::shutdown(listener_, SHUT_RDWR);
    ::close(listener_);
    if (client_ >= 0) ::shutdown(client_, SHUT_RDWR);
    thread_.join();
  }
  std::string address() const { return "127.0.0.1:" + std::to_string(port_); }

  std::mutex lock;
  std::string token, client_id;
  std::vector<std::string> subscribed;  // "source|exchange|code"

 private:
  bool read(std::string& out, size_t n) {
    out.assign(n, '\0');
    for (size_t got = 0; got < n;) {
      const ssize_t r = ::recv(client_, &out[got], n - got, 0);
      if (r <= 0) return false;
      got += static_cast<size_t>(r);
    }
    return true;
  }
  void send(uint16_t type, const std::string& body) {
    const std::string frame = qp::make_frame(type, 0, body);
    ::send(client_, frame.data(), frame.size(), MSG_NOSIGNAL);
  }
  void serve() {
    client_ = ::accept(listener_, nullptr, nullptr);
    if (client_ < 0) return;
    std::string head, body;
    while (read(head, qp::kHeaderSize)) {
      const auto header = qp::unpack_header(head);
      if (!read(body, header.body_len)) break;
      if (header.msg_type == qp::REQ_LOGIN) {
        {
          std::lock_guard<std::mutex> guard(lock);
          client_id = cut(body, 0, 32);
          token = body.substr(40, get<uint32_t>(body, 32));
        }
        send(qp::RSP_LOGIN, login_rsp(token == "tok" ? 0 : 20));
      } else if (header.msg_type == qp::REQ_SUBSCRIBE) {
        size_t count;
        {
          std::lock_guard<std::mutex> guard(lock);
          subscribed.push_back(cut(body, 0, 16) + "|" + cut(body, 16, 16) + "|" + cut(body, 32, 32));
          count = subscribed.size();
        }
        send(qp::RSP_SUBSCRIBE, sub_rsp(body));
        if (count == 2) {  // inst_seq 1, then 3: record 2 never arrived
          std::string batch;
          put<uint32_t>(batch, 2);
          put<uint32_t>(batch, 0);
          batch += quote_record(10, 1, 1688.0) + quote_record(12, 3, 1690.5);
          send(qp::RECORD_BATCH, batch);
        }
      }
    }
    ::close(client_);
  }

  int listener_ = -1;
  int client_ = -1;
  int port_ = 0;
  std::thread thread_;
};

struct Recorder : lf::QuoteSpi {
  lf::QuoteApi* api = nullptr;
  std::mutex lock;
  std::vector<lf::LoginRsp> logins;
  std::vector<lf::SubRsp> subs;
  std::vector<lf::Quote> quotes;
  std::vector<lf::SequenceGap> gaps;

  void on_rsp_login(const lf::LoginRsp& rsp, int) override {
    {
      std::lock_guard<std::mutex> guard(lock);
      logins.push_back(rsp);
    }
    if (rsp.error_id == 0) api->subscribe({"600519.XSHG", "000001.XSHE", "600519.XSHG"});
  }
  void on_rsp_subscribe(const lf::SubRsp& rsp, int) override {
    std::lock_guard<std::mutex> guard(lock);
    subs.push_back(rsp);
  }
  void on_depth_market_data(const lf::Quote& quote, const lf::RecordEnvelope&) override {
    std::lock_guard<std::mutex> guard(lock);
    quotes.push_back(quote);
  }
  void on_sequence_gap(const lf::SequenceGap& gap) override {
    std::lock_guard<std::mutex> guard(lock);
    gaps.push_back(gap);
  }
  template <typename F>
  bool wait(F&& done, double seconds = 5.0) {
    const auto until = std::chrono::steady_clock::now() + std::chrono::duration<double>(seconds);
    while (std::chrono::steady_clock::now() < until) {
      {
        std::lock_guard<std::mutex> guard(lock);
        if (done()) return true;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    std::lock_guard<std::mutex> guard(lock);
    return done();
  }
};

}  // namespace

TEST(QuoteApi, LogsInSubscribesByOrderBookIdAndReportsGaps) {
  FakeGateway gateway;
  lf::QuoteApi api(true, "tester");
  Recorder spi;
  spi.api = &api;
  api.register_spi(&spi);
  api.login("tok");
  ASSERT_EQ(api.connect(gateway.address()), 0);
  ASSERT_TRUE(spi.wait([&] { return spi.quotes.size() >= 2 && spi.subs.size() >= 2; }));
  {
    std::lock_guard<std::mutex> guard(gateway.lock);
    EXPECT_EQ(gateway.token, "tok");
    EXPECT_EQ(gateway.client_id, "tester");
    // duplicates once, in order; the wire carries code and exchange apart
    EXPECT_EQ(gateway.subscribed, (std::vector<std::string>{"|XSHG|600519", "|XSHE|000001"}));
  }
  std::lock_guard<std::mutex> guard(spi.lock);
  ASSERT_EQ(spi.logins.size(), 1u);
  EXPECT_EQ(spi.logins[0].max_subscriptions, 50);
  EXPECT_EQ(spi.subs[0].order_book_id(), "600519.XSHG");
  EXPECT_EQ(spi.subs[1].order_book_id(), "000001.XSHE");
  EXPECT_EQ(spi.subs[0].source, "auto");
  EXPECT_EQ(spi.quotes[0].order_book_id(), "600519.XSHG");
  EXPECT_DOUBLE_EQ(spi.quotes[1].last_price, 1690.5);
  ASSERT_EQ(spi.gaps.size(), 1u);
  EXPECT_EQ(spi.gaps[0].order_book_id(), "600519.XSHG");
  EXPECT_EQ(spi.gaps[0].expected_inst_seq, 2u);
  EXPECT_EQ(spi.gaps[0].received_inst_seq, 3u);
  api.disconnect();
  EXPECT_FALSE(api.connected());
}

TEST(QuoteApi, ABadCodeSendsNothing) {
  lf::QuoteApi api;
  EXPECT_THROW(api.subscribe({"600519.XSHG", "600519"}), std::invalid_argument);
  EXPECT_THROW(api.subscribe("AAPL.US"), std::invalid_argument);
  EXPECT_THROW(api.subscribe(std::vector<std::string>{}), std::invalid_argument);
  EXPECT_EQ(api.subscribe("600519.XSHG"), 0);  // valid, but no connection: dropped, replayed after login
}

// ---------------------------------------------------------------- a revoked ticket

namespace {

//: Accepts connection after connection; logs in any ticket not revoked (else TOKEN_REVOKED, 23).
//: Revoke() sends NOTIFY_SESSION_CLOSED (revoked) for the current ticket and drops the link.
class RevokingGateway {
 public:
  RevokingGateway() {
    listener_ = ::socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(listener_, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (::bind(listener_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0 || ::listen(listener_, 4) != 0)
      throw std::runtime_error("cannot listen");
    socklen_t size = sizeof(addr);
    ::getsockname(listener_, reinterpret_cast<sockaddr*>(&addr), &size);
    port_ = ntohs(addr.sin_port);
    thread_ = std::thread([this] { serve(); });
  }
  ~RevokingGateway() {
    stopping_ = true;
    ::shutdown(listener_, SHUT_RDWR);
    ::close(listener_);
    const int fd = client_;
    if (fd >= 0) ::shutdown(fd, SHUT_RDWR);
    thread_.join();
  }
  std::string address() const { return "127.0.0.1:" + std::to_string(port_); }
  void revoke() {
    {
      std::lock_guard<std::mutex> guard(lock);
      revoked.push_back(tokens.back());
    }
    std::string body;
    put<int32_t>(body, 2);
    fixed(body, "ticket revoked", 64);
    send(qp::NOTIFY_SESSION_CLOSED, body);
    ::shutdown(client_, SHUT_RDWR);
  }

  std::mutex lock;
  std::vector<std::string> tokens, revoked, subscribed;  // subscribed: "connection|code"
  int connections = 0;

 private:
  bool read(int fd, std::string& out, size_t n) {
    out.assign(n, '\0');
    for (size_t got = 0; got < n;) {
      const ssize_t r = ::recv(fd, &out[got], n - got, 0);
      if (r <= 0) return false;
      got += static_cast<size_t>(r);
    }
    return true;
  }
  void send(uint16_t type, const std::string& body) {
    const std::string frame = qp::make_frame(type, 0, body);
    ::send(client_, frame.data(), frame.size(), MSG_NOSIGNAL);
  }
  void serve() {
    while (!stopping_) {
      const int fd = ::accept(listener_, nullptr, nullptr);
      if (fd < 0) return;
      client_ = fd;
      int connection;
      {
        std::lock_guard<std::mutex> guard(lock);
        connection = ++connections;
      }
      std::string head, body;
      while (read(fd, head, qp::kHeaderSize)) {
        const auto header = qp::unpack_header(head);
        if (!read(fd, body, header.body_len)) break;
        if (header.msg_type == qp::REQ_LOGIN) {
          const std::string token = body.substr(40, get<uint32_t>(body, 32));
          bool refused;
          {
            std::lock_guard<std::mutex> guard(lock);
            tokens.push_back(token);
            refused = std::find(revoked.begin(), revoked.end(), token) != revoked.end();
          }
          send(qp::RSP_LOGIN, login_rsp(refused ? 23 : 0));
        } else if (header.msg_type == qp::REQ_SUBSCRIBE) {
          {
            std::lock_guard<std::mutex> guard(lock);
            subscribed.push_back(std::to_string(connection) + "|" + cut(body, 32, 32));
          }
          send(qp::RSP_SUBSCRIBE, sub_rsp(body));
        }
      }
      client_ = -1;
      ::close(fd);
    }
  }

  int listener_ = -1;
  std::atomic<int> client_{-1};
  std::atomic<bool> stopping_{false};
  int port_ = 0;
  std::thread thread_;
};

struct Resubscriber : lf::QuoteSpi {
  lf::QuoteApi* api = nullptr;
  std::mutex lock;
  std::vector<int> logins;  // error_id of every login answer
  void on_rsp_login(const lf::LoginRsp& rsp, int) override {
    {
      std::lock_guard<std::mutex> guard(lock);
      logins.push_back(rsp.error_id);
    }
    if (rsp.error_id == 0) api->subscribe("600519.XSHG");
  }
};

template <typename F>
bool eventually(F&& done, double seconds = 5.0) {
  const auto until = std::chrono::steady_clock::now() + std::chrono::duration<double>(seconds);
  while (std::chrono::steady_clock::now() < until) {
    if (done()) return true;
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
  return done();
}

}  // namespace

TEST(QuoteApi, ARevokedTicketIsReplacedAndSubscriptionsComeBack) {
  RevokingGateway gateway;
  lf::QuoteApi api;
  Resubscriber spi;
  spi.api = &api;
  api.register_spi(&spi);
  // a new ticket after every revocation (the provider is also asked at login and on connecting)
  api.login(lf::TokenProvider([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return "t" + std::to_string(gateway.revoked.size());
  }));
  ASSERT_EQ(api.connect(gateway.address()), 0);
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.subscribed.size() == 1;
  }));
  gateway.revoke();
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.subscribed.size() == 2;
  }));
  std::lock_guard<std::mutex> guard(gateway.lock);
  EXPECT_EQ(gateway.tokens, (std::vector<std::string>{"t0", "t1"}));
  EXPECT_EQ(gateway.subscribed, (std::vector<std::string>{"1|600519", "2|600519"}));
  api.disconnect();
}

TEST(QuoteApi, ACallerRefusedTicketsStopsAfterRevocation) {
  RevokingGateway gateway;
  lf::QuoteApi api;
  Resubscriber spi;
  spi.api = &api;
  api.register_spi(&spi);
  std::atomic<int> refused{0};
  api.login(lf::TokenProvider([&]() -> std::string {
    {
      std::lock_guard<std::mutex> guard(gateway.lock);
      if (gateway.revoked.empty()) return "t0";
    }
    ++refused;
    throw lf::RpcError(2001, "real-time quote access is suspended for this caller", "PermissionError");
  }));
  ASSERT_EQ(api.connect(gateway.address()), 0);
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.subscribed.size() == 1;
  }));
  gateway.revoke();
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.connections >= 2;
  }));
  std::this_thread::sleep_for(std::chrono::seconds(1));
  {
    std::lock_guard<std::mutex> guard(gateway.lock);
    EXPECT_EQ(gateway.tokens, std::vector<std::string>{"t0"});  // no login with an empty or revoked ticket
  }
  EXPECT_EQ(refused.load(), 1);  // refused once: not asked again and again
  api.disconnect();
}

TEST(QuoteApi, AFixedTicketRevokedIsNotRetriedForever) {
  RevokingGateway gateway;
  lf::QuoteApi api;
  Resubscriber spi;
  spi.api = &api;
  api.register_spi(&spi);
  api.login("fixed");
  ASSERT_EQ(api.connect(gateway.address()), 0);
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.subscribed.size() == 1;
  }));
  gateway.revoke();
  ASSERT_TRUE(eventually([&] {
    std::lock_guard<std::mutex> guard(gateway.lock);
    return gateway.tokens.size() >= 2;
  }));
  std::this_thread::sleep_for(std::chrono::seconds(1));
  {
    std::lock_guard<std::mutex> guard(gateway.lock);
    EXPECT_EQ(gateway.tokens, (std::vector<std::string>{"fixed", "fixed"}));  // once more, refused as revoked
  }
  std::lock_guard<std::mutex> guard(spi.lock);
  EXPECT_EQ(spi.logins.back(), 23);
  api.disconnect();
}
