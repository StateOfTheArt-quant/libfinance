// Python: libfinance/api/industry.py.
#include "libfinance/industry.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_industry_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call("get_industry_constituents",
                      {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

Table get_instrument_industry(const Codes& order_book_ids, const std::optional<std::string>& source,
                              const std::optional<int>& level, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_instrument_industry", {{"order_book_ids", detail::as_given(order_book_ids)},
                                                        {"source", detail::text_or_null(source)},
                                                        {"level", level ? Json(*level) : Json(nullptr)},
                                                        {"as_of", detail::iso_or_null(as_of)}});
}

Table get_industry_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_industry_weights",
                            {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
