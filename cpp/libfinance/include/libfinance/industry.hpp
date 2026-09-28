// Industry classification (Python: api/industry.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: The members of one industry.
Json get_industry(const std::string& industry, const std::string& source = "sw",
                  const std::optional<DateLike>& date = std::nullopt,
                  const std::optional<std::string>& market = std::nullopt);
//: The whole classification.
Table get_industry_mapping(const std::string& source = "sw", const std::optional<DateLike>& date = std::nullopt,
                           const std::optional<std::string>& market = std::nullopt);

}  // namespace libfinance
