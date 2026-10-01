// The libfinance wire protocol, client side (Python: libfinance/client.py). Self-contained: a TCP
// connection, frames, msgpack (nlohmann::json) and LZ4 frames (liblz4) -- nothing of the server's.
//
//   frame:   [4B body_len][1B type][4B request_id][1B flags][payload]   (big-endian; body_len = 6 + payload)
//   request: msgpack {"function": name, "args": {...}}, LZ4-frame compressed (flags 0x01)
//   answer:  msgpack envelope {"status": "ok", "result": ...} or {"status": "error", "code", "message", "kind"}
//   PING from the server is answered with PONG.
#pragma once

#include <mutex>
#include <string>

#include "libfinance/errors.hpp"
#include "libfinance/types.hpp"

namespace libfinance::wire {

//: A call that never got the server's answer (connection, timeout, an undecodable frame): it may be
//: tried again on a new connection. The server's own refusals are plain RpcError and are not.
class TransportError : public RpcError {
 public:
  using RpcError::RpcError;
};
constexpr int kConnectionFailed = -1;
constexpr int kTimeout = -2;
constexpr int kProtocolError = -3;

class Connection {
 public:
  Connection(std::string host, int port, int timeout_seconds = 300);
  ~Connection();
  Connection(const Connection&) = delete;
  Connection& operator=(const Connection&) = delete;

  //: One request and its answer, unwrapped: the result, or RpcError with the server's code, message
  //: and kind. Calls are serialized; a broken connection is re-opened on the next call.
  Json call(const std::string& function, const Json& args);

 private:
  void open();
  void close();
  void send_frame(uint8_t type, uint32_t request_id, uint8_t flags, const std::string& payload);
  bool read_frame(uint8_t& type, uint32_t& request_id, uint8_t& flags, std::string& payload);

  std::string host_;
  int port_;
  int timeout_seconds_;
  int socket_ = -1;
  uint32_t next_id_ = 0;
  std::mutex lock_;
};

}  // namespace libfinance::wire
