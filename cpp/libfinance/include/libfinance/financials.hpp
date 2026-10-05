// Point-in-time financials and derived financial metrics (Python: api/financials.py). Quarters are
// written like "2026q1".
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: statements: "latest" or "all".
Table get_pit_financials_ex(const Codes& order_book_ids, const Codes& fields, const std::string& start_quarter,
                            const std::string& end_quarter, const std::optional<DateLike>& as_of = std::nullopt,
                            const std::string& statements = "latest");
//: Derived financial metrics on each trading day (columns order_book_id, date, one per field): a
//: day's value comes from the latest report visible after its close. No dates: the latest trading day.
Table get_financial_metrics(const Codes& order_book_ids, const Codes& fields,
                            const std::optional<DateLike>& start_date = std::nullopt,
                            const std::optional<DateLike>& end_date = std::nullopt);

}  // namespace libfinance
