// Industry of securities and index weights (Python: api/index_components.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: The industries order_book_ids belong to on as_of; no source / level means every classification / level.
Table get_instrument_industry(const Codes& order_book_ids, const std::optional<std::string>& source = std::nullopt,
                              const std::optional<int>& level = std::nullopt,
                              const std::optional<DateLike>& as_of = std::nullopt);
Table get_index_weights(const std::string& index_code, const std::optional<DateLike>& date = std::nullopt);

}  // namespace libfinance
