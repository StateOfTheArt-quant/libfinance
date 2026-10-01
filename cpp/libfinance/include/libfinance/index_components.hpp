// Index members and weights (Python: api/index_components.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: The members of one index (``000300.XSHG``) on as_of: their order_book_ids, or null.
Json get_index_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);
//: The indices order_book_ids belong to on as_of; no source means every publisher.
Table get_instrument_indices(const Codes& order_book_ids, const std::optional<std::string>& source = std::nullopt,
                             const std::optional<DateLike>& as_of = std::nullopt);
//: The weights of one index's members on as_of, each with its methodology.
Table get_index_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
