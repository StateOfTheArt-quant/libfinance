// Python: libfinance/api/shares.py.
#include "libfinance/shares.hpp"

#include "internal.hpp"

namespace libfinance {

namespace {

//: The unified share fields (pyshares field_codes), every market.
const std::vector<std::string> kShareFields = {"free_float_shares",  "issued_shares",      "preferred_shares",
                                               "restricted_shares",  "shares_outstanding", "tradable_shares"};

}  // namespace

Table get_shares(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                 const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Json ids = detail::order_book_ids(order_book_ids);
  Json names;
  if (fields.given()) {
    detail::check_items_in(fields.values(), kShareFields, "fields",
                           "('free_float_shares', 'issued_shares', 'preferred_shares', 'restricted_shares', "
                           "'shares_outstanding', 'tradable_shares')");
    names = fields.values();
  }
  const Json start = detail::iso_or_null(start_date), end = detail::iso_or_null(end_date);
  detail::check_date_range(start, end);
  return detail::call_table("get_shares",
                            {{"order_book_ids", ids}, {"start_date", start}, {"end_date", end}, {"fields", names},
                             {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
