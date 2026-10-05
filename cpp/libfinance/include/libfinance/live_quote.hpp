// Latest quote snapshots (Python: api/live_quote.py).
#pragma once

#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: {order_book_id: quote fields, or null when the security has no snapshot}. One snapshot per call.
Json get_last_quotes(const std::vector<std::string>& order_book_ids);

}  // namespace libfinance
