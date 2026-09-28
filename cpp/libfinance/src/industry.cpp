// Python: libfinance/api/industry.py.
#include "libfinance/industry.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_industry(const std::string& industry, const std::string& source, const std::optional<DateLike>& date,
                  const std::optional<std::string>& market) {
  return detail::call("get_industry", {{"industry", industry},
                                       {"source", source},
                                       {"date", detail::iso_or_null(date)},
                                       {"market", detail::text_or_null(market)}});
}

Table get_industry_mapping(const std::string& source, const std::optional<DateLike>& date,
                           const std::optional<std::string>& market) {
  return detail::call_table("get_industry_mapping", {{"source", source},
                                                     {"date", detail::iso_or_null(date)},
                                                     {"market", detail::text_or_null(market)}});
}

}  // namespace libfinance
