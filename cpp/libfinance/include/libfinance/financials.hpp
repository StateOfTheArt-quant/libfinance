// Point-in-time financials (Python: api/financials.py). Quarters are written like "2026q1".
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: statements: "latest" or "all".
Table get_pit_financials_ex(const Codes& order_book_ids, const Codes& fields, const std::string& start_quarter,
                            const std::string& end_quarter, const std::optional<DateLike>& as_of = std::nullopt,
                            const std::string& statements = "latest");
Table get_factor(const Codes& order_book_ids, const Codes& factors, const std::string& start_quarter,
                 const std::string& end_quarter, const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
