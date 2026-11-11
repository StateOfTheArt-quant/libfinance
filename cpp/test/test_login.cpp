// RpcClient::login against a loopback server that, like the real one, keeps the caller's level on the
// connection: a new connection starts anonymous, so the client must log in again after a reconnect.
#include <gtest/gtest.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <cstring>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include <lz4frame.h>

#include <libfinance/client.hpp>
#include <libfinance/errors.hpp>

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

//: Answers `login` (password "right" -> level 100) and any other function with this connection's
//: level; closes each connection after `per_connection` requests.
class LoginServer {
 public:
  explicit LoginServer(int per_connection) : per_connection_(per_connection) {
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
    ::listen(listener_, 8);
    thread_ = std::thread([this] { serve(); });
  }
  ~LoginServer() {
    ::shutdown(listener_, SHUT_RDWR);
    ::close(listener_);
    thread_.join();
  }
  int port() const { return port_; }
  std::vector<std::string> logins() {
    std::lock_guard<std::mutex> guard(lock_);
    return logins_;
  }

 private:
  void serve() {
    for (int connection = 1;; ++connection) {
      const int fd = ::accept(listener_, nullptr, nullptr);
      if (fd < 0) return;
      int level = 0;
      for (int answered = 0; answered < per_connection_; ++answered) {
        char header[4];
        if (!read_exact(fd, header, 4)) break;
        const uint32_t body = ntohl(*reinterpret_cast<uint32_t*>(header));
        std::string data(body, '\0');
        if (!read_exact(fd, data.data(), body)) break;
        const uint32_t request_id = ntohl(*reinterpret_cast<const uint32_t*>(data.data() + 1));
        const std::string payload = data.substr(6);
        const Json request = Json::from_msgpack(static_cast<uint8_t>(data[5]) & 0x01 ? lz4_decompress(payload) : payload);
        Json result;
        if (request.at("function") == "login") {
          {
            std::lock_guard<std::mutex> guard(lock_);
            logins_.push_back(request.at("args").at("username").get<std::string>());
          }
          if (request.at("args").at("password") == "right") {
            level = 100;
            result = {{"status", "successful"}, {"level", level}, {"user_id", 7}};
          } else {
            result = {{"status", "failed"}, {"message", "Invalid username or password"}};
          }
        } else {
          result = {{"level", level}, {"connection", connection}};
        }
        const std::vector<uint8_t> packed = Json::to_msgpack(Json{{"status", "ok"}, {"code", 0}, {"result", result}});
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
      ::close(fd);  // what a stopped (drained) instance does to the connection
    }
  }

  int per_connection_;
  int listener_ = -1;
  int port_ = 0;
  std::thread thread_;
  std::mutex lock_;
  std::vector<std::string> logins_;
};

}  // namespace

TEST(Login, RaisesTheLevelAndSurvivesAReconnect) {
  LoginServer server(2);
  lf::RpcClient client("127.0.0.1", server.port());
  EXPECT_EQ(client.login("admin", "right").at("level"), 100);
  EXPECT_EQ(client.call("whoami", Json::object()), (Json{{"level", 100}, {"connection", 1}}));
  // the server closed the first connection: the next call reconnects and logs in before it is sent
  EXPECT_EQ(client.call("whoami", Json::object()), (Json{{"level", 100}, {"connection", 2}}));
  EXPECT_EQ(server.logins(), (std::vector<std::string>{"admin", "admin"}));
}

TEST(Login, AWrongPasswordThrowsAndStaysAnonymous) {
  LoginServer server(10);
  lf::RpcClient client("127.0.0.1", server.port());
  try {
    client.login("admin", "wrong");
    FAIL() << "expected LoginError";
  } catch (const lf::LoginError& error) {
    EXPECT_NE(std::string(error.what()).find("Invalid username or password"), std::string::npos);
  }
  EXPECT_EQ(client.call("whoami", Json::object()).at("level"), 0);
}
