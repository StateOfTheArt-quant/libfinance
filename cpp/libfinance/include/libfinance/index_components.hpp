// Industry of securities and index weights (Python: api/index_components.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

Table get_instrument_industry(const Codes& order_book_ids, const std::optional<DateLike>& date = std::nullopt,
                              const std::string& source = "sw", int level = 1);
Table get_index_weights(const std::string& index_code, const std::optional<DateLike>& date = std::nullopt);

}  // namespace libfinance
