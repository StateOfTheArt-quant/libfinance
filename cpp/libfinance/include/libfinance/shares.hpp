// Share structure (Python: api/shares.py).
#pragma once

#include <optional>

#include "libfinance/types.hpp"

namespace libfinance {

//: fields within total, total_a, circulation_a, non_circulation_a, free_circulation, preferred_shares.
Table get_shares(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                 const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {});

}  // namespace libfinance
