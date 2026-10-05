// Python: libfinance/api/exfactor.py.
#include "libfinance/exfactor.hpp"

#include "internal.hpp"

namespace libfinance {

Table get_ex_factor(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                    const std::optional<DateLike>& end_date) {
  const Json ids = detail::order_book_ids(order_book_ids);
  const Json start = detail::iso_or_null(start_date), end = detail::iso_or_null(end_date);
  if (start.is_string() && end.is_string() && start.get<std::string>() > end.get<std::string>())
    throw std::invalid_argument("start_date must not be after end_date");
  return detail::call_table("get_ex_factor", {{"order_book_ids", ids}, {"start_date", start}, {"end_date", end}});
}

}  // namespace libfinance
