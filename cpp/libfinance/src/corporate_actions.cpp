// Python: libfinance/api/corporate_actions.py. The four functions share one set of arguments.
#include "libfinance/corporate_actions.hpp"

#include "internal.hpp"

namespace libfinance {

namespace {

//: `_args`: codes (at least one), dates as ISO days in order, fields as a list.
Json arguments(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
               const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Json ids = detail::order_book_ids(order_book_ids);
  const Json start = detail::iso_or_null(start_date), end = detail::iso_or_null(end_date);
  detail::check_date_range(start, end);
  return {{"order_book_ids", ids},
          {"start_date", start},
          {"end_date", end},
          {"fields", detail::list_or_null(fields, "fields")},
          {"as_of", detail::iso_or_null(as_of)}};
}

}  // namespace

Table get_dividends(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                    const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_dividends", arguments(order_book_ids, start_date, end_date, fields, as_of));
}

Table get_splits(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                 const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_splits", arguments(order_book_ids, start_date, end_date, fields, as_of));
}

Table get_allotments(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                     const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_allotments", arguments(order_book_ids, start_date, end_date, fields, as_of));
}

Table get_spinoffs(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                   const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_spinoffs", arguments(order_book_ids, start_date, end_date, fields, as_of));
}

}  // namespace libfinance
