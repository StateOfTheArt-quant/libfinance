// Shares: the unified fields, one set for every market, and the daily turnover rate (Python:
// libfinance/api/shares.py).
#pragma once

#include <optional>

#include "libfinance/types.hpp"

namespace libfinance {

//: Shares per trading day, security level: columns order_book_id, date, then one per field (null where
//: a market does not publish it). `fields` within free_float_shares, issued_shares, preferred_shares,
//: restricted_shares, shares_outstanding, tradable_shares; none for all. `as_of` is the knowledge cutoff.
Table get_shares(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                 const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {},
                 const std::optional<DateLike>& as_of = std::nullopt);

//: Daily turnover rate: columns order_book_id, date, turnover_rate -- unadjusted volume / the A-share free
//: float (else the A-share tradable shares) effective that day, a fraction (0.01 is 1%); a suspended
//: session has no row, a day without a share count a null. One date: that day; none: the latest trading
//: day with bars in the last two weeks.
Table get_turnover_rate(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                        const std::optional<DateLike>& end_date = std::nullopt);

}  // namespace libfinance
