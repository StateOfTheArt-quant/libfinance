// Python: libfinance/api/calendar.py.
#include "libfinance/calendar.hpp"

#include <algorithm>
#include <initializer_list>
#include <memory>

#include "internal.hpp"

namespace libfinance {

namespace {

//: The sessions and the range the release confirms, fetched together and cached together: fetched
//: apart, a switch of release in between would pair one release's range with another's sessions.
struct Calendar {
  std::vector<Date> sessions;
  Date lower;
  Date upper;
};

Date day_of(const Json& value) { return DateLike(value.get<std::string>().substr(0, 10)).date(); }

std::shared_ptr<const Calendar> calendar(const std::string& market) {
  static detail::TtlCache<std::shared_ptr<const Calendar>> cache(std::chrono::hours(24));
  return cache.get(market, [&] {
    Json sessions = detail::call("get_trading_calendar", {{"market", market}});
    if (sessions.is_string()) sessions = Json::parse(sessions.get<std::string>());  // a JSON text of the list
    const Json window = detail::call("get_calendar_coverage", {{"market", market}});
    auto out = std::make_shared<Calendar>();
    for (const Json& value : sessions) out->sessions.push_back(day_of(value));
    out->lower = day_of(window.at("history_start"));
    out->upper = day_of(window.at("confirmed_through"));
    return std::shared_ptr<const Calendar>(out);
  });
}

//: The sessions, once every date asked about is known to lie within the confirmed range.
std::shared_ptr<const Calendar> sessions(const std::string& market, std::initializer_list<Date> dates) {
  auto found = calendar(market);
  for (Date value : dates)
    if (value < found->lower || value > found->upper)
      throw CalendarCoverageError(market + " 的查询 " + value.iso() + " 超出 release 确认范围 " + found->lower.iso() +
                                  ".." + found->upper.iso());
  return found;
}

size_t lower_bound(const std::vector<Date>& sessions, Date date) {
  return static_cast<size_t>(std::lower_bound(sessions.begin(), sessions.end(), date) - sessions.begin());
}

size_t upper_bound(const std::vector<Date>& sessions, Date date) {
  return static_cast<size_t>(std::upper_bound(sessions.begin(), sessions.end(), date) - sessions.begin());
}

}  // namespace

std::vector<Date> get_all_trading_dates(const std::string& market) { return calendar(market)->sessions; }

CalendarCoverage get_calendar_coverage(const std::string& market) {
  const auto found = calendar(market);
  return {found->lower, found->upper};
}

std::vector<Date> get_trading_dates(const DateLike& start_date, const DateLike& end_date, const std::string& market) {
  const auto found = sessions(market, {start_date.date(), end_date.date()});
  const size_t left = lower_bound(found->sessions, start_date.date());
  const size_t right = upper_bound(found->sessions, end_date.date());
  if (left >= right) return {};
  return {found->sessions.begin() + static_cast<long>(left), found->sessions.begin() + static_cast<long>(right)};
}

Date get_previous_trading_date(const DateLike& date, int n, const std::string& market) {
  const auto found = sessions(market, {date.date()});
  const size_t position = lower_bound(found->sessions, date.date());
  if (static_cast<long>(position) < n)
    throw CalendarCoverageError(date.iso() + " 之前没有第 " + std::to_string(n) + " 个交易日；release 的第一个交易日是 " +
                                found->sessions.front().iso());
  return found->sessions[position - static_cast<size_t>(n)];
}

Date get_next_trading_date(const DateLike& date, int n, const std::string& market) {
  const auto found = sessions(market, {date.date()});
  const size_t position = upper_bound(found->sessions, date.date());
  if (position + static_cast<size_t>(n) > found->sessions.size())
    throw CalendarCoverageError(date.iso() + " 之后没有第 " + std::to_string(n) + " 个交易日；release 确认到 " +
                                found->upper.iso());
  return found->sessions[position + static_cast<size_t>(n) - 1];
}

bool is_trading_date(const DateLike& date, const std::string& market) {
  const auto found = sessions(market, {date.date()});
  const size_t position = lower_bound(found->sessions, date.date());
  return position < found->sessions.size() && found->sessions[position] == date.date();
}

std::vector<Date> get_n_trading_dates_until(const DateLike& date, int n, const std::string& market) {
  const auto found = sessions(market, {date.date()});
  const size_t position = upper_bound(found->sessions, date.date());
  const size_t first = static_cast<long>(position) >= n ? position - static_cast<size_t>(n) : 0;
  return {found->sessions.begin() + static_cast<long>(first), found->sessions.begin() + static_cast<long>(position)};
}

int count_trading_dates(const DateLike& start_date, const DateLike& end_date, const std::string& market) {
  const auto found = sessions(market, {start_date.date(), end_date.date()});
  return static_cast<int>(upper_bound(found->sessions, end_date.date())) -
         static_cast<int>(lower_bound(found->sessions, start_date.date()));
}

}  // namespace libfinance
