// Daily factor exposures (Python: api/factors.py): qlib, alpha158 and the Barra CNE5 style, industry and
// country factors, served by factors-daybar. Factor names are spelled in full: a library
// "owner/library[@rev]" (all its factors) or a factor "owner/library/factor[@rev]".
#pragma once

#include <optional>
#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: Columns order_book_id, date, then one float32 column per factor (a library expands to its factors'
//: full names). start_date == end_date is that day's cross section. A cross-sectional factor (the Barra
//: styles) is computed over `universe` (codes; default: each day's A-share market); a code asked for
//: outside it has NaN. Time-series factors ignore `universe`.
Table get_factor_exposure(const Codes& order_book_ids, const Codes& factor_names, const DateLike& start_date,
                          const DateLike& end_date, const Codes& universe = {});

//: The factor libraries: columns name, version, factors (count), description.
Table list_factor_libraries();

//: The full names of the factors of `library`, or of every library, with their revision
//: ("system/barra-cne5/SIZE@v2.0.0"; without "@revision" a name reads the current one).
std::vector<std::string> list_factors(const std::optional<std::string>& library = std::nullopt);

}  // namespace libfinance
