// The connection to a libfinance server (Python client: libfinance/client.py).
//
// The first call connects to LIBFINANCE_HOST:LIBFINANCE_PORT, else libfinance.tech:8080 -- the live
// production service. init_client() points elsewhere before that first call:
//
//   libfinance::init_client("127.0.0.1", 8080);
#pragma once

#include <functional>
#include <memory>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: LIBFINANCE_HOST, or libfinance.tech.
std::string default_host();
//: LIBFINANCE_PORT, or 8080.
int default_port();

//: Connects the process-wide client, unless one is already connected (Python's init_client).
void init_client(const std::string& host = default_host(), int port = default_port());

//: One connection to a libfinance server; calls from many threads share it.
class RpcClient {
 public:
  RpcClient(const std::string& host, int port);
  ~RpcClient();
  RpcClient(const RpcClient&) = delete;
  RpcClient& operator=(const RpcClient&) = delete;

  //: Calls a server function with keyword arguments and returns its result, as it came (a table
  //: answer is {"type": "arrow" | "pandas", "data": ...}; see as_table). Connection failures are
  //: retried twice; what the server refuses throws RpcError at once.
  Json call(const std::string& function, const Json& args) const;

 private:
  struct Connection;
  std::unique_ptr<Connection> connection_;
};

//: The process-wide client, connected on first use.
RpcClient& get_client();

//: A table answer as an arrow::Table: Arrow IPC from the C++ server, or pandas' orient=table JSON
//: from the Python one. Anything else throws std::invalid_argument.
Table as_table(const Json& answer);

//: Where warnings go (Python's warnings.warn); stderr by default.
void set_warning_handler(std::function<void(const std::string&)> handler);

//: Drops every versioned cache (Python's libfinance.utils.cache.clear_all). A change of the
//: server's data version drops them by itself; this is for tests and debugging.
void clear_cache();

}  // namespace libfinance
