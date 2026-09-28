// Concepts and their members (Python: api/concept_components.py).
#pragma once

#include <optional>
#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: Cached by the server's data version.
Table get_concept_meta(const std::string& source = "THS", const Codes& fields = {},
                       const std::optional<std::string>& market = std::nullopt);
//: Warns about concept ids get_concept_meta does not know (the server answers them with no rows).
Table get_concept_weights(const std::vector<std::string>& concept_ids,
                          const std::optional<DateLike>& as_of = std::nullopt, const std::string& source = "THS",
                          const std::optional<std::string>& market = std::nullopt);

}  // namespace libfinance
