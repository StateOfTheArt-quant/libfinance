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
//: `timeout_seconds` bounds each request (a timed-out request is not retried: the server keeps
//: executing it); `max_connections` is how many requests the client keeps in flight at once.
void init_client(const std::string& host = default_host(), int port = default_port(), int timeout_seconds = 300,
                 int max_connections = 8);

//: A client of one libfinance server; calls from many threads share it and run in parallel, each on
//: one of up to `max_connections` connections (opened as needed, the first one by the constructor,
//: which throws RpcError when the server cannot be reached within 5 s).
//:
//: After fork() the child gets connections of its own: the parent's are left to the parent (sharing
//: them would let either process read the other's answers).
class RpcClient {
 public:
  RpcClient(const std::string& host, int port, int timeout_seconds = 300, int max_connections = 8);
  ~RpcClient();
  RpcClient(const RpcClient&) = delete;
  RpcClient& operator=(const RpcClient&) = delete;

  //: Calls a server function with keyword arguments and returns its result, as it came (a table
  //: answer is {"type": "arrow" | "pandas", "data": ...}; see as_table). Connection failures are
  //: retried twice on a fresh connection; a timeout and what the server refuses throw RpcError at once.
  Json call(const std::string& function, const Json& args) const;
  //: Logs in; later calls get the account's level, and a reconnect logs in again by itself.
  //: Returns {"status": "successful", "level", "user_id"}; throws LoginError when refused.
  Json login(const std::string& username, const std::string& password);

 private:
  struct Connection;
  std::unique_ptr<Connection> connection_;
};

//: The process-wide client, connected on first use.
RpcClient& get_client();

//: Logs the process-wide client in (Python's libfinance.login); see RpcClient::login.
Json login(const std::string& username, const std::string& password);

//: A table answer as an arrow::Table: Arrow IPC from the C++ server, or pandas' orient=table JSON
//: from the Python one. Anything else throws std::invalid_argument.
Table as_table(const Json& answer);

//: Where warnings go (Python's warnings.warn); stderr by default.
void set_warning_handler(std::function<void(const std::string&)> handler);

//: Drops every versioned cache (Python's libfinance.utils.cache.clear_all). A change of the
//: server's data version drops them by itself; this is for tests and debugging.
void clear_cache();

}  // namespace libfinance
