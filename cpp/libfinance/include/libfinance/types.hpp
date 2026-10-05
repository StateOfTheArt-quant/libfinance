// The value types of the libfinance C++ API.
//
// Where the Python client takes "a date-like value" or "one code or a list of codes", C++ takes a
// DateLike or a Codes, both built implicitly from what a caller naturally writes:
//
//   libfinance::get_price("600000.XSHG", "2025-06-02", 20250606);
//   libfinance::get_price({"600000.XSHG", "AAPL.US"}, libfinance::Date::ymd(2025, 6, 2), "2025-06-06");
#pragma once

#include <cstdint>
#include <initializer_list>
#include <memory>
#include <ostream>
#include <string>
#include <vector>

#include <arrow/table.h>
#include <nlohmann/json.hpp>

namespace libfinance {

//: A Python dict / list answer.
using Json = nlohmann::json;
//: A pandas DataFrame answer.
using Table = std::shared_ptr<arrow::Table>;

//: A calendar day (a pandas Timestamp at midnight in the Python client).
class Date {
 public:
  Date() = default;
  static Date ymd(int year, unsigned month, unsigned day);
  static Date from_days(int32_t days_since_epoch);

  int year() const;
  unsigned month() const;
  unsigned day() const;
  int32_t days_since_epoch() const { return days_; }
  //: "YYYY-MM-DD"
  std::string iso() const;

  friend bool operator==(Date a, Date b) { return a.days_ == b.days_; }
  friend bool operator!=(Date a, Date b) { return a.days_ != b.days_; }
  friend bool operator<(Date a, Date b) { return a.days_ < b.days_; }
  friend bool operator<=(Date a, Date b) { return a.days_ <= b.days_; }
  friend bool operator>(Date a, Date b) { return a.days_ > b.days_; }
  friend bool operator>=(Date a, Date b) { return a.days_ >= b.days_; }

 private:
  explicit Date(int32_t days) : days_(days) {}
  int32_t days_ = 0;
};

std::ostream& operator<<(std::ostream& out, Date date);

//: A date argument (Python's `to_date`): "2025-06-02", "2025/06/02", "20250602",
//: "2025-06-02 15:30:00" (the time is dropped), the integer 20250602, or a Date.
//: Anything else throws std::invalid_argument.
class DateLike {
 public:
  DateLike(const char* text);         // NOLINT(google-explicit-constructor): a date is written as text
  DateLike(const std::string& text);  // NOLINT(google-explicit-constructor)
  DateLike(Date date) : date_(date) {}  // NOLINT(google-explicit-constructor)
  DateLike(int yyyymmdd);             // NOLINT(google-explicit-constructor)

  Date date() const { return date_; }
  std::string iso() const { return date_.iso(); }

 private:
  Date date_;
};

//: One code or a list of codes (Python's `str or list[str]`), or none given (Python's None):
//:
//:   f("600000.XSHG")            one
//:   f({"600000.XSHG", "AAPL.US"})  a list
//:   f()  /  f({})                 none: the parameter's default
class Codes {
 public:
  Codes() = default;
  Codes(const char* one) : values_{one}, given_(true), single_(true) {}         // NOLINT(google-explicit-constructor)
  Codes(std::string one) : values_{std::move(one)}, given_(true), single_(true) {}  // NOLINT(google-explicit-constructor)
  Codes(std::vector<std::string> many) : values_(std::move(many)), given_(true) {}  // NOLINT(google-explicit-constructor)
  Codes(std::initializer_list<std::string> many) : values_(many), given_(true) {}

  //: false for None.
  bool given() const { return given_; }
  //: Given as one string rather than a list.
  bool single() const { return single_; }
  const std::vector<std::string>& values() const { return values_; }

 private:
  std::vector<std::string> values_;
  bool given_ = false;
  bool single_ = false;
};

}  // namespace libfinance
