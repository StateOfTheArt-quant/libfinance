// Adjustment factors per ex-date (Python: api/exfactor.py).
#pragma once

#include <optional>

#include "libfinance/types.hpp"

namespace libfinance {

//: ex_factor per ex-date and the cumulative ex_cum_factor (from 1 before the first event).
Table get_ex_factor(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                    const std::optional<DateLike>& end_date = std::nullopt);

}  // namespace libfinance
