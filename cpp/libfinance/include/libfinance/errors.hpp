// Errors of the libfinance C++ API.
//
// A bad argument, refused before any request is sent, is std::invalid_argument (Python's
// ValueError). What the server refuses is an RpcError carrying the server's code and, from a server
// that reports one, its error kind (CoverageError, UnknownInstrumentError, CapabilityUnavailable...).
#pragma once

#include <stdexcept>
#include <string>

namespace libfinance {

class RpcError : public std::runtime_error {
 public:
  RpcError(int code, std::string message, std::string kind = "")
      : std::runtime_error("RpcError(code=" + std::to_string(code) + "): " + message),
        code_(code),
        message_(std::move(message)),
        kind_(std::move(kind)) {}

  int code() const { return code_; }
  const std::string& message() const { return message_; }
  //: The server's error kind; empty when the server does not report one.
  const std::string& kind() const { return kind_; }

 private:
  int code_;
  std::string message_;
  std::string kind_;
};

//: A calendar query outside the release's confirmed range. It is not "no trading that day":
//: nobody has published that day yet, so any answer would be a guess.
class CalendarCoverageError : public std::invalid_argument {
 public:
  using std::invalid_argument::invalid_argument;
};

}  // namespace libfinance
