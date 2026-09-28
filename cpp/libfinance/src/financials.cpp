// Python: libfinance/api/financials.py.
#include "libfinance/financials.hpp"

#include <algorithm>
#include <cctype>

#include "internal.hpp"

namespace libfinance {

namespace {

//: The statement versions the server knows (upstream financialmetrics' whitelist).
const std::vector<std::string> kStatements = {"latest", "all"};

//: `_quarter`: "2026-Q1" -> "2026q1"; something without a q is refused.
std::string quarter(const std::string& value, const std::string& name) {
  std::string text;
  for (char c : value)
    if (c != '-') text.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
  if (text.find('q') == std::string::npos)
    throw std::invalid_argument(name + ": expected a quarter like '2026q1', got '" + value + "'");
  return text;
}

std::vector<std::string> at_least_one(const Codes& values, const std::string& name, const std::string& what) {
  std::vector<std::string> list = detail::list_of(values, name);
  if (list.empty()) throw std::invalid_argument(name + ": at least one " + what + " expected");
  return list;
}

}  // namespace

Table get_pit_financials_ex(const Codes& order_book_ids, const Codes& fields, const std::string& start_quarter,
                            const std::string& end_quarter, const std::optional<DateLike>& as_of,
                            const std::string& statements) {
  const Json ids = detail::order_book_ids(order_book_ids);
  const Json names = at_least_one(fields, "fields", "field");
  if (std::find(kStatements.begin(), kStatements.end(), statements) == kStatements.end())
    throw std::invalid_argument("statements: expect value in ('latest', 'all')");
  return detail::call_table("get_pit_financials_ex", {{"order_book_ids", ids},
                                                      {"fields", names},
                                                      {"start_quarter", quarter(start_quarter, "start_quarter")},
                                                      {"end_quarter", quarter(end_quarter, "end_quarter")},
                                                      {"as_of", detail::iso_or_null(as_of)},
                                                      {"statements", statements}});
}

Table get_factor(const Codes& order_book_ids, const Codes& factors, const std::string& start_quarter,
                 const std::string& end_quarter, const std::optional<DateLike>& as_of) {
  const Json ids = detail::order_book_ids(order_book_ids);
  const Json names = at_least_one(factors, "factors", "factor");
  return detail::call_table("get_factor", {{"order_book_ids", ids},
                                           {"factors", names},
                                           {"start_quarter", quarter(start_quarter, "start_quarter")},
                                           {"end_quarter", quarter(end_quarter, "end_quarter")},
                                           {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
