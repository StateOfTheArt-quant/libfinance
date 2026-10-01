// Python: libfinance/api/index_components.py.
#include "libfinance/index_components.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_index_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call("get_index_constituents", {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

Table get_instrument_indices(const Codes& order_book_ids, const std::optional<std::string>& source,
                             const std::optional<DateLike>& as_of) {
  return detail::call_table("get_instrument_indices", {{"order_book_ids", detail::as_given(order_book_ids)},
                                                       {"source", detail::text_or_null(source)},
                                                       {"as_of", detail::iso_or_null(as_of)}});
}

Table get_index_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_index_weights",
                            {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
