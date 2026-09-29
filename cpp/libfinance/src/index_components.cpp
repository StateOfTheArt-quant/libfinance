// Python: libfinance/api/index_components.py.
#include "libfinance/index_components.hpp"

#include "internal.hpp"

namespace libfinance {

Table get_instrument_industry(const Codes& order_book_ids, const std::optional<std::string>& source,
                              const std::optional<int>& level, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_instrument_industry", {{"order_book_ids", detail::as_given(order_book_ids)},
                                                        {"source", detail::text_or_null(source)},
                                                        {"level", level ? Json(*level) : Json(nullptr)},
                                                        {"as_of", detail::iso_or_null(as_of)}});
}

//: Monthly anchor snapshots upstream; for another day the server re-weights the latest anchor
//: before it by each member's adjusted return.
Table get_index_weights(const std::string& index_code, const std::optional<DateLike>& date) {
  return detail::call_table("get_index_weights", {{"index_code", index_code}, {"date", detail::iso_or_null(date)}});
}

}  // namespace libfinance
