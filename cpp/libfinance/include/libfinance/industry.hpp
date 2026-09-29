// Industry membership and weights (Python: api/industry.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: The members of one industry (``801780.SW``) on as_of: their order_book_ids, or null.
Json get_industry_constituents(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);
//: The weights of one industry's members on as_of, each with its methodology.
Table get_industry_weights(const std::string& order_book_id, const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
