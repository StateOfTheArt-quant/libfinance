// Python: libfinance/api/industry.py.
#include "libfinance/industry.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_industry_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call("get_industry_constituents",
                      {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

Table get_industry_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_industry_weights",
                            {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
