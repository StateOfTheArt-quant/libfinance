// 交易日历：A 股与美股的交易日、日期偏移与日历覆盖范围（与 example/python/01_calendar.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // A 股日历确认到哪天（不是行情更新到哪天）
      const auto coverage = lf::get_calendar_coverage("cn");
      std::cout << coverage.history_start << " .. " << coverage.confirmed_through << "\n";
    }

    {  // 美股日历的覆盖范围
      const auto coverage = lf::get_calendar_coverage("us");
      std::cout << coverage.history_start << " .. " << coverage.confirmed_through << "\n";
    }

    {  // 当前日历包含的全部交易日
      const auto dates = lf::get_all_trading_dates("cn");
      std::cout << dates.size() << " " << dates.front() << " " << dates.back() << "\n";
    }

    {  // 区间内的 A 股交易日
      show(lf::get_trading_dates("2024-01-01", "2024-01-31", "cn"));
    }

    {  // 同一区间换成美股，交易日不同
      show(lf::get_trading_dates("2024-01-01", "2024-01-31", "us"));
    }

    {  // 周一开市
      show(lf::is_trading_date("2024-01-08", "cn"));
    }

    {  // 周日休市
      show(lf::is_trading_date("2024-01-07", "cn"));
    }

    {  // 严格早于输入日的上一个交易日
      show(lf::get_previous_trading_date("2024-01-08"));
    }

    {  // n=3：往前第三个交易日，不是减三天
      show(lf::get_previous_trading_date("2024-01-08", 3));
    }

    {  // 严格晚于输入日的下一个交易日
      show(lf::get_next_trading_date("2024-01-05"));
    }

    {  // n=3：往后第三个交易日
      show(lf::get_next_trading_date("2024-01-05", 3));
    }

    {  // 截至周一（含）的最近 5 个交易日
      show(lf::get_n_trading_dates_until("2024-01-08", 5));
    }

    {  // 截至周日：从此前最近的交易日往回数
      show(lf::get_n_trading_dates_until("2024-01-07", 5));
    }

    {  // 只要样本数时直接计数
      show(lf::count_trading_dates("2024-01-01", "2024-01-31", "cn"));
    }
  });
}
