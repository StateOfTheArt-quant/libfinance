// A long answer on a slow link must not cost the connection (PERF-03). The server PINGs every 15 s and
// drops a connection whose last PONG is older than 45 s, but its PING is queued behind the answer it is
// writing; the client therefore sends an unsolicited PONG every 10 s while an answer is arriving.
#include <gtest/gtest.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include <libfinance/client.hpp>

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

//: Answers the first request with `size` bytes trickled over `seconds`; counts the client's PONGs
//: that arrive while the answer is being sent.
class TricklingServer {
 public:
  TricklingServer(size_t size, int pieces, double seconds) : size_(size), pieces_(pieces), seconds_(seconds) {
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
    ::listen(listener_, 1);
    thread_ = std::thread([this] { serve(); });
  }
  ~TricklingServer() {
    ::shutdown(listener_, SHUT_RDWR);
    ::close(listener_);
    thread_.join();
    if (reader_.joinable()) reader_.join();
  }
  int port() const { return port_; }
  int pongs_during_answer() const { return pongs_.load(); }

 private:
  void serve() {
    const int fd = ::accept(listener_, nullptr, nullptr);
    if (fd < 0) return;
    std::atomic<uint32_t> request_id{0};
    std::atomic<bool> requested{false}, sending{false};
    reader_ = std::thread([&, fd] {
      for (;;) {
        char header[4];
        if (!read_exact(fd, header, 4)) return;
        const uint32_t body = ntohl(*reinterpret_cast<uint32_t*>(header));
        std::string data(body, '\0');
        if (!read_exact(fd, data.data(), body)) return;
        if (data[0] == 0x01) {
          request_id = ntohl(*reinterpret_cast<const uint32_t*>(data.data() + 1));
          requested = true;
        } else if (data[0] == 0x04 && sending) {
          ++pongs_;
        }
      }
    });
    while (!requested) std::this_thread::sleep_for(std::chrono::milliseconds(5));
    const std::vector<uint8_t> packed =
        Json::to_msgpack(Json{{"status", "ok"}, {"code", 0}, {"result", std::string(size_, 'x')}});
    std::string frame(4, '\0');
    const uint32_t length = htonl(static_cast<uint32_t>(6 + packed.size()));
    std::memcpy(frame.data(), &length, 4);
    frame.push_back(0x02);
    const uint32_t id = htonl(request_id.load());
    frame.append(reinterpret_cast<const char*>(&id), 4);
    frame.push_back(0x00);
    frame.append(packed.begin(), packed.end());
    sending = true;
    const size_t step = (frame.size() + pieces_ - 1) / pieces_;
    for (size_t start = 0; start < frame.size(); start += step) {
      ::send(fd, frame.data() + start, std::min(step, frame.size() - start), MSG_NOSIGNAL);
      std::this_thread::sleep_for(std::chrono::duration<double>(seconds_ / pieces_));
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    sending = false;
    ::shutdown(fd, SHUT_RDWR);
    ::close(fd);
  }

  size_t size_;
  int pieces_;
  double seconds_;
  int listener_ = -1;
  int port_ = 0;
  std::thread thread_, reader_;
  std::atomic<int> pongs_{0};
};

}  // namespace

TEST(Keepalive, AnUnsolicitedPongWhileALongAnswerArrives) {
  TricklingServer server(200000, 60, 12.0);  // longer than the 10 s keepalive interval
  lf::RpcClient client("127.0.0.1", server.port(), 60, 1);
  const Json answer = client.call("get_price", Json::object());
  EXPECT_EQ(answer.get<std::string>().size(), 200000u);
  EXPECT_GE(server.pongs_during_answer(), 1);
}

TEST(Keepalive, NoPongForAQuickAnswer) {
  TricklingServer server(50000, 2, 0.1);
  lf::RpcClient client("127.0.0.1", server.port(), 60, 1);
  EXPECT_EQ(client.call("get_price", Json::object()).get<std::string>().size(), 50000u);
  EXPECT_EQ(server.pongs_during_answer(), 0);
}
