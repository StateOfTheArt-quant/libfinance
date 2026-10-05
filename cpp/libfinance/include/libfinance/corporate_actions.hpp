// Corporate actions: dividends, splits, allotments, spin-offs (Python: api/corporate_actions.py).
#pragma once

#include <optional>

#include "libfinance/types.hpp"

namespace libfinance {

Table get_dividends(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                    const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {},
                    const std::optional<DateLike>& as_of = std::nullopt);
Table get_splits(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                 const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {},
                 const std::optional<DateLike>& as_of = std::nullopt);
Table get_allotments(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                     const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {},
                     const std::optional<DateLike>& as_of = std::nullopt);
//: US only; a CN code is refused by the server as an unsupported market.
Table get_spinoffs(const Codes& order_book_ids, const std::optional<DateLike>& start_date = std::nullopt,
                   const std::optional<DateLike>& end_date = std::nullopt, const Codes& fields = {},
                   const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
