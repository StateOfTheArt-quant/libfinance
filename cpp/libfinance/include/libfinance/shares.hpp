// Shares: the unified fields, one set for every market (Python: libfinance/api/shares.py).
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

}  // namespace libfinance
