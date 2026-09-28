// Trading calendar (Python: libfinance/api/calendar.py).
//
// The server gives two primitives: the sessions (get_trading_calendar) and the range the release
// confirms (get_calendar_coverage). Everything here is a search over the sorted sessions, done
// locally; both are fetched together and cached for a day. A date outside the confirmed range is a
// CalendarCoverageError, never "no trading": nobody has published that day yet.
#pragma once

#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: Every session of the calendar.
std::vector<Date> get_all_trading_dates(const std::string& market = "cn");

struct CalendarCoverage {
  Date history_start;
  Date confirmed_through;
};
//: How far the release confirms the calendar.
CalendarCoverage get_calendar_coverage(const std::string& market = "cn");

//: The sessions within [start_date, end_date].
std::vector<Date> get_trading_dates(const DateLike& start_date, const DateLike& end_date,
                                    const std::string& market = "cn");
//: The n-th session strictly before `date`.
Date get_previous_trading_date(const DateLike& date, int n = 1, const std::string& market = "cn");
//: The n-th session strictly after `date`.
Date get_next_trading_date(const DateLike& date, int n = 1, const std::string& market = "cn");
bool is_trading_date(const DateLike& date, const std::string& market = "cn");
//: The last n sessions up to and including `date` (fewer when the history is shorter).
std::vector<Date> get_n_trading_dates_until(const DateLike& date, int n, const std::string& market = "cn");
//: The number of sessions within [start_date, end_date].
int count_trading_dates(const DateLike& start_date, const DateLike& end_date, const std::string& market = "cn");

}  // namespace libfinance
