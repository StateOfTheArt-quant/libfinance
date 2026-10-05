#include <gtest/gtest.h>

#include <libfinance/types.hpp>

using libfinance::Codes;
using libfinance::Date;
using libfinance::DateLike;

TEST(Date, RoundTripsThroughIso) {
  for (const std::string day : {"1970-01-01", "1990-12-19", "2000-02-29", "2025-06-02", "2100-03-01"})
    EXPECT_EQ(DateLike(day).iso(), day);
  EXPECT_EQ(Date::ymd(2025, 6, 2).days_since_epoch(), DateLike("2025-06-02").date().days_since_epoch());
  EXPECT_LT(Date::ymd(2025, 6, 2), Date::ymd(2025, 6, 3));
}

TEST(DateLike, TakesWhatPythonsToDateTakes) {
  const Date day = Date::ymd(2025, 6, 2);
  EXPECT_EQ(DateLike("2025-06-02").date(), day);
  EXPECT_EQ(DateLike("2025/06/02").date(), day);
  EXPECT_EQ(DateLike("20250602").date(), day);
  EXPECT_EQ(DateLike(20250602).date(), day);
  EXPECT_EQ(DateLike("2025-06-02 15:30:00").date(), day);
  EXPECT_EQ(DateLike("2025-06-02T00:00:00.000").date(), day);
  EXPECT_EQ(DateLike(day).date(), day);
}

TEST(DateLike, RefusesWhatIsNotADate) {
  for (const char* text : {"", "2025", "2025-13-01", "2025-02-30", "June 2", "2025-06-02x"})
    EXPECT_THROW(DateLike{text}, std::invalid_argument) << text;
}

TEST(Codes, OneAListOrNone) {
  const Codes one = "600000.XSHG";
  EXPECT_TRUE(one.given());
  EXPECT_TRUE(one.single());
  const Codes many = {"600000.XSHG", "AAPL.US"};
  EXPECT_FALSE(many.single());
  EXPECT_EQ(many.values().size(), 2u);
  const Codes none = {};
  EXPECT_FALSE(none.given());
  const Codes empty = std::vector<std::string>{};
  EXPECT_TRUE(empty.given());
  EXPECT_TRUE(empty.values().empty());
}
