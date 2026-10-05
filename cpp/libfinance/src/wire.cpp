#include "wire.hpp"

#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <memory>

#include <lz4frame.h>

namespace libfinance::wire {

namespace {

constexpr uint8_t kRequest = 0x01, kResponse = 0x02, kPing = 0x03, kPong = 0x04;
constexpr uint8_t kLz4 = 0x01;
constexpr size_t kMetaSize = 6;                       // type(1) + request_id(4) + flags(1)
constexpr uint32_t kMaxBody = 2u * 1024 * 1024 * 1024 - 1;  // guards against a corrupt length only

void put_u32(std::string& out, uint32_t value) {
  for (int shift = 24; shift >= 0; shift -= 8) out.push_back(static_cast<char>((value >> shift) & 0xff));
}

uint32_t get_u32(const unsigned char* in) {
  return (uint32_t(in[0]) << 24) | (uint32_t(in[1]) << 16) | (uint32_t(in[2]) << 8) | uint32_t(in[3]);
}

std::string lz4_compress(const std::string& raw) {
  std::string out(LZ4F_compressFrameBound(raw.size(), nullptr), '\0');
  const size_t size = LZ4F_compressFrame(out.data(), out.size(), raw.data(), raw.size(), nullptr);
  if (LZ4F_isError(size)) throw TransportError(kProtocolError, std::string("lz4: ") + LZ4F_getErrorName(size));
  out.resize(size);
  return out;
}

std::string lz4_decompress(const std::string& frame) {
  LZ4F_dctx* context = nullptr;
  if (LZ4F_isError(LZ4F_createDecompressionContext(&context, LZ4F_VERSION)))
    throw TransportError(kProtocolError, "lz4: cannot create a decompression context");
  std::unique_ptr<LZ4F_dctx, decltype(&LZ4F_freeDecompressionContext)> owned(context, LZ4F_freeDecompressionContext);
  std::string out;
  std::string block(1 << 20, '\0');
  const char* in = frame.data();
  size_t left = frame.size();
  while (left > 0) {
    size_t produced = block.size(), consumed = left;
    const size_t hint = LZ4F_decompress(context, block.data(), &produced, in, &consumed, nullptr);
    if (LZ4F_isError(hint)) throw TransportError(kProtocolError, std::string("lz4: ") + LZ4F_getErrorName(hint));
    out.append(block.data(), produced);
    in += consumed;
    left -= consumed;
    if (hint == 0) break;  // the frame is complete
  }
  return out;
}

}  // namespace

Connection::Connection(std::string host, int port, int timeout_seconds)
    : host_(std::move(host)), port_(port), timeout_seconds_(timeout_seconds) {
  open();
}

Connection::~Connection() { close(); }

void Connection::open() {
  addrinfo hints{};
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;
  addrinfo* found = nullptr;
  const std::string port = std::to_string(port_);
  if (const int status = getaddrinfo(host_.c_str(), port.c_str(), &hints, &found); status != 0)
    throw TransportError(kConnectionFailed, "cannot resolve " + host_ + ": " + gai_strerror(status));
  std::unique_ptr<addrinfo, decltype(&freeaddrinfo)> addresses(found, freeaddrinfo);
  std::string reason = "no address";
  for (addrinfo* address = found; address != nullptr; address = address->ai_next) {
    const int fd = ::socket(address->ai_family, address->ai_socktype, address->ai_protocol);
    if (fd < 0) continue;
    timeval timeout{timeout_seconds_, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    if (::connect(fd, address->ai_addr, address->ai_addrlen) == 0) {
      const int on = 1;
      setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &on, sizeof(on));
      socket_ = fd;
      return;
    }
    reason = std::strerror(errno);
    ::close(fd);
  }
  throw TransportError(kConnectionFailed, "cannot connect to " + host_ + ":" + port + ": " + reason);
}

void Connection::close() {
  if (socket_ >= 0) ::close(socket_);
  socket_ = -1;
}

void Connection::send_frame(uint8_t type, uint32_t request_id, uint8_t flags, const std::string& payload) {
  std::string frame;
  frame.reserve(4 + kMetaSize + payload.size());
  put_u32(frame, static_cast<uint32_t>(kMetaSize + payload.size()));
  frame.push_back(static_cast<char>(type));
  put_u32(frame, request_id);
  frame.push_back(static_cast<char>(flags));
  frame += payload;
  for (size_t sent = 0; sent < frame.size();) {
    const ssize_t n = ::send(socket_, frame.data() + sent, frame.size() - sent, MSG_NOSIGNAL);
    if (n <= 0) throw TransportError(kConnectionFailed, std::string("send failed: ") + std::strerror(errno));
    sent += static_cast<size_t>(n);
  }
}

bool Connection::read_frame(uint8_t& type, uint32_t& request_id, uint8_t& flags, std::string& payload) {
  auto read_exact = [&](char* out, size_t size) {
    for (size_t got = 0; got < size;) {
      const ssize_t n = ::recv(socket_, out + got, size - got, 0);
      if (n == 0) throw TransportError(kConnectionFailed, "the server closed the connection");
      if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK)
          throw TransportError(kTimeout, "no answer within " + std::to_string(timeout_seconds_) + "s");
        if (errno == EINTR) continue;
        throw TransportError(kConnectionFailed, std::string("receive failed: ") + std::strerror(errno));
      }
      got += static_cast<size_t>(n);
    }
  };
  unsigned char length[4];
  read_exact(reinterpret_cast<char*>(length), 4);
  const uint32_t body = get_u32(length);
  if (body < kMetaSize || body > kMaxBody) throw TransportError(kProtocolError, "invalid frame length " + std::to_string(body));
  std::string data(body, '\0');
  read_exact(data.data(), body);
  const auto* meta = reinterpret_cast<const unsigned char*>(data.data());
  type = meta[0];
  request_id = get_u32(meta + 1);
  flags = meta[5];
  payload.assign(data, kMetaSize, std::string::npos);
  return true;
}

Json Connection::call(const std::string& function, const Json& args) {
  std::lock_guard<std::mutex> guard(lock_);
  if (socket_ < 0) open();
  try {
    const uint32_t id = ++next_id_;
    const std::vector<uint8_t> packed = Json::to_msgpack(Json{{"function", function}, {"args", args}});
    send_frame(kRequest, id, kLz4, lz4_compress(std::string(packed.begin(), packed.end())));
    for (;;) {
      uint8_t type = 0, flags = 0;
      uint32_t request_id = 0;
      std::string payload;
      read_frame(type, request_id, flags, payload);
      if (type == kPing) {
        send_frame(kPong, request_id, 0, "");
        continue;
      }
      if (type != kResponse || request_id != id) continue;  // a PONG, or an answer nobody waits for
      const std::string raw = (flags & kLz4) ? lz4_decompress(payload) : payload;
      Json envelope = Json::from_msgpack(raw);
      if (!envelope.is_object()) return envelope;
      if (envelope.value("status", "") == "error") {
        const Json message = envelope.value("message", Json("unknown error"));
        throw RpcError(envelope.value("code", -1), message.is_string() ? message.get<std::string>() : message.dump(),
                       envelope.value("kind", Json()).is_string() ? envelope["kind"].get<std::string>() : "");
      }
      return envelope.contains("result") ? envelope["result"] : envelope;
    }
  } catch (const TransportError&) {
    close();  // the stream is in an unknown state: start over next time
    throw;
  } catch (const Json::exception& error) {
    close();
    throw TransportError(kProtocolError, std::string("cannot decode the answer: ") + error.what());
  }
}

}  // namespace libfinance::wire
