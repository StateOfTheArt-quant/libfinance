// Python: libfinance/api/theme.py.
#include "libfinance/theme.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_theme_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call("get_theme_constituents", {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

Table get_instrument_themes(const Codes& order_book_ids, const std::optional<std::string>& source,
                            const std::optional<DateLike>& as_of) {
  return detail::call_table("get_instrument_themes", {{"order_book_ids", detail::as_given(order_book_ids)},
                                                      {"source", detail::text_or_null(source)},
                                                      {"as_of", detail::iso_or_null(as_of)}});
}

Table get_theme_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of) {
  return detail::call_table("get_theme_weights",
                            {{"order_book_id", order_book_id}, {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
