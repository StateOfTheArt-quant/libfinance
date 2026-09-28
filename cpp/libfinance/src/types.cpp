#include "libfinance/types.hpp"

#include <cctype>
#include <cstdio>
#include <stdexcept>

namespace libfinance {

namespace {

// H. Hinnant's days_from_civil / civil_from_days.
int32_t days_from_civil(int year, unsigned month, unsigned day) {
  year -= month <= 2;
  const int era = (year >= 0 ? year : year - 399) / 400;
  const unsigned year_of_era = static_cast<unsigned>(year - era * 400);
  const unsigned day_of_year = (153 * (month > 2 ? month - 3 : month + 9) + 2) / 5 + day - 1;
  const unsigned day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
  return era * 146097 + static_cast<int>(day_of_era) - 719468;
}

struct Civil {
  int year;
  unsigned month;
  unsigned day;
};

Civil civil_from_days(int32_t days) {
  const int z = days + 719468;
  const int era = (z >= 0 ? z : z - 146096) / 146097;
  const unsigned day_of_era = static_cast<unsigned>(z - era * 146097);
  const unsigned year_of_era = (day_of_era - day_of_era / 1460 + day_of_era / 36524 - day_of_era / 146096) / 365;
  const unsigned day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
  const unsigned mp = (5 * day_of_year + 2) / 153;
  const unsigned month = mp < 10 ? mp + 3 : mp - 9;
  return {static_cast<int>(year_of_era) + era * 400 + (month <= 2), month, day_of_year - (153 * mp + 2) / 5 + 1};
}

bool valid(int year, unsigned month, unsigned day) {
  static const unsigned kDays[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const bool leap = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
  return day <= (month == 2 && leap ? 29u : kDays[month - 1]);
}

[[noreturn]] void refuse(const std::string& text) {
  throw std::invalid_argument("expect a datetime like object, got '" + text + "'");
}

unsigned number(const std::string& text, size_t from, size_t length) {
  unsigned value = 0;
  for (size_t i = from; i < from + length; ++i) {
    if (!std::isdigit(static_cast<unsigned char>(text[i]))) refuse(text);
    value = value * 10 + static_cast<unsigned>(text[i] - '0');
  }
  return value;
}

//: "YYYY-MM-DD" / "YYYY/MM/DD" / "YYYY.MM.DD" / "YYYYMMDD", optionally followed by a time.
Date parse(const std::string& raw) {
  const auto first = raw.find_first_not_of(" \t");
  if (first == std::string::npos) refuse(raw);
  const std::string text = raw.substr(first);
  unsigned year = 0, month = 0, day = 0;
  size_t end = 0;
  if (text.size() >= 10 && (text[4] == '-' || text[4] == '/' || text[4] == '.') && text[7] == text[4]) {
    year = number(text, 0, 4), month = number(text, 5, 2), day = number(text, 8, 2), end = 10;
  } else if (text.size() >= 8) {
    year = number(text, 0, 4), month = number(text, 4, 2), day = number(text, 6, 2), end = 8;
  } else {
    refuse(raw);
  }
  // what may follow the day: a time ("T15:30" / " 15:30:00"), nothing else
  if (end < text.size() && text[end] != 'T' && text[end] != ' ') refuse(raw);
  if (!valid(static_cast<int>(year), month, day)) refuse(raw);
  return Date::ymd(static_cast<int>(year), month, day);
}

}  // namespace

Date Date::ymd(int year, unsigned month, unsigned day) { return Date(days_from_civil(year, month, day)); }

Date Date::from_days(int32_t days_since_epoch) { return Date(days_since_epoch); }

int Date::year() const { return civil_from_days(days_).year; }
unsigned Date::month() const { return civil_from_days(days_).month; }
unsigned Date::day() const { return civil_from_days(days_).day; }

std::string Date::iso() const {
  const Civil civil = civil_from_days(days_);
  char text[32];
  std::snprintf(text, sizeof(text), "%04d-%02u-%02u", civil.year, civil.month, civil.day);
  return text;
}

std::ostream& operator<<(std::ostream& out, Date date) { return out << date.iso(); }

DateLike::DateLike(const char* text) : date_(parse(text == nullptr ? "" : text)) {}

DateLike::DateLike(const std::string& text) : date_(parse(text)) {}

DateLike::DateLike(int yyyymmdd) : date_(parse(std::to_string(yyyymmdd))) {}

}  // namespace libfinance
