// Python: warn_if_clamped from libfinance/utils/cache.py, shared by the functions whose free tier
// clamps start_date (get_price, get_factor_exposure).
#include <ctime>

#include "internal.hpp"

namespace libfinance::detail {

namespace {

//: today minus years / months / days, the month-end clipped (dateutil's relativedelta).
Date months_back(int years, int months, int days) {
  const std::time_t now = std::time(nullptr);
  std::tm local{};
  localtime_r(&now, &local);
  int month_index = (local.tm_year + 1900) * 12 + local.tm_mon - years * 12 - months;
  const int year = month_index / 12;
  const unsigned month = static_cast<unsigned>(month_index % 12) + 1;
  unsigned day = static_cast<unsigned>(local.tm_mday);
  while (day > 28 && Date::ymd(year, month, day).month() != month) --day;
  return Date::from_days(Date::ymd(year, month, day).days_since_epoch() - days);
}

}  // namespace

//: `limits_for`: this caller's limits on a function (describe_capabilities); {} when unknown.
Json limits_for(const std::string& api_name) {
  static detail::VersionedCache<Json> cache;
  try {
    const Json described = cache.get("", [] { return detail::call("describe_capabilities", Json::object()); });
    for (const Json& item : described.value("capabilities", Json::array()))
      if (item.value("api", Json()) == api_name || item.value("name", Json()) == api_name)
        return item.value("limits", Json::object());
  } catch (const std::exception&) {
  }
  return Json::object();
}

//: `warn_if_clamped`: say so when the caller's tier will pull start_date up to its boundary.
void warn_if_clamped(const std::string& api_name, const std::string& start_date) {
  const Json window = limits_for(api_name).value("clamp_date_window", Json());
  if (!window.is_object()) return;
  const std::string boundary =
      months_back(window.value("years", 0), window.value("months", 0), window.value("days", 0)).iso();
  if (start_date >= boundary) return;
  detail::warn(api_name + ": 可查区间的起点是 " + boundary + "，比它更早的 start_date=" + start_date +
               " 会被服务端夹到边界（end_date 早于边界时也会一起上拉，结果可能是空表）。");
}

//: `warn_if_truncated`: say so when the caller's tier keeps only the first max_count codes.
void warn_if_truncated(const std::string& api_name, std::size_t count) {
  const Json limit = limits_for(api_name).value("clamp_instrument_count", Json());
  if (!limit.is_object() || !limit.value("max_count", Json()).is_number_integer()) return;
  const auto max_count = limit.value("max_count", 0);
  if (max_count <= 0 || count <= static_cast<std::size_t>(max_count)) return;
  detail::warn(api_name + ": 当前权限一次最多 " + std::to_string(max_count) + " 个代码，传入的 " + std::to_string(count) +
               " 个只有前 " + std::to_string(max_count) + " 个会被查询；请分批调用。");
}

}  // namespace libfinance::detail
