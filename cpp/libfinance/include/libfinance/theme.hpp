// Theme members and weights (Python: api/theme.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: The members of one theme (``300900.THS``) on as_of: their order_book_ids, or null.
Json get_theme_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);
//: The themes order_book_ids belong to on as_of; no source means every catalogue.
Table get_instrument_themes(const Codes& order_book_ids, const std::optional<std::string>& source = std::nullopt,
                            const std::optional<DateLike>& as_of = std::nullopt);
//: The weights of one theme's members on as_of, each with its methodology.
Table get_theme_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
