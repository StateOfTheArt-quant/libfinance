// 交易日历：市场、日期区间与交易日偏移（Python：example/python/01_calendar.py）。
//
// 日期接受日期字符串；market 默认 cn，美股传 us。
// 区间查询包含两端；前后偏移不包含输入日；截至某日的窗口包含该日（若为交易日）。
#include "show.hpp"

int main() {
  return run([] {
    // [get_calendar_coverage]
    // 日历确认到哪天？这不是行情已更新到哪天。超出范围会抛 CalendarCoverageError。
    for (const char* market : {"cn", "us"}) {
      const lf::CalendarCoverage coverage = lf::get_calendar_coverage(market);
      std::cout << market << ": " << coverage.history_start << " .. " << coverage.confirmed_through << "\n";
    }
    // [/get_calendar_coverage]

    // [get_all_trading_dates]
    // 获取当前日历包含的全部交易日。
    std::cout << lf::get_all_trading_dates("cn").size() << " trading days\n";
    // [/get_all_trading_dates]

    // [get_trading_dates]
    // 相同自然日区间，切换市场后交易日可能不同。
    show(lf::get_trading_dates("2024-01-01", "2024-01-31", "cn"));
    show(lf::get_trading_dates("2024-01-01", "2024-01-31", "us"));
    // [/get_trading_dates]

    // [is_trading_date]
    // 判断某天是否开市；不要把周末简单等同于所有非交易日。
    show(lf::is_trading_date("2024-01-08", "cn"));
    show(lf::is_trading_date("2024-01-07", "cn"));
    // [/is_trading_date]

    // [get_previous_trading_date]
    // 严格早于输入日；n=3 表示第三个交易日，不是减三天。
    show(lf::get_previous_trading_date("2024-01-08"));
    show(lf::get_previous_trading_date("2024-01-08", 3));
    // [/get_previous_trading_date]

    // [get_next_trading_date]
    // 严格晚于输入日；用 n 调整结算或调仓的交易日偏移。
    show(lf::get_next_trading_date("2024-01-05"));
    show(lf::get_next_trading_date("2024-01-05", 3));
    // [/get_next_trading_date]

    // [get_n_trading_dates_until]
    // 截至周一的最近 5 个交易日包含周一；截至周日则从此前最近交易日结束。
    show(lf::get_n_trading_dates_until("2024-01-08", 5));
    show(lf::get_n_trading_dates_until("2024-01-07", 5));
    // [/get_n_trading_dates_until]

    // [count_trading_dates]
    // 只需要样本数时直接计数，不用拿自然日天数代替交易日天数。
    show(lf::count_trading_dates("2024-01-01", "2024-01-31", "cn"));
    // [/count_trading_dates]
  });
}
