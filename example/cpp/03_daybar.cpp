// 日频行情：股票与指数、字段、复权方式与查询窗口（Python：example/python/03_daybar.py）。
//
// get_price(order_book_ids, start_date, end_date, frequency, fields, skip_suspended, include_now,
//           adjust_type, adjust_orig) -> Table：order_book_id、datetime、permanent_id 与所选字段。
// 股票与指数可以混在一批里：股票按 adjust_type 复权，指数原样返回。
#include "show.hpp"

int main() {
  return run([] {
    // [get_price]
    // 1. 单只股票只取收盘价与成交量，缩小返回列数。默认前复权。
    show(lf::get_price("000001.XSHE", "2024-03-01", "2024-03-11", "1d", {"close", "volume"}));
    // 2. 股票与指数混在一批，取 OHLC 字段。
    show(lf::get_price({"000001.XSHE", "600000.XSHG", "000300.XSHG"}, "2024-03-01", "2024-03-11", "1d",
                       {"open", "high", "low", "close"}),
         0);
    // 3. 固定标的与日期，只改变 adjust_type，比较原始价、前复权与后复权。
    // 成交额叫 turnover；volume 随复权缩放，turnover 不随复权缩放。
    for (const char* adjustment : {"none", "pre", "post"}) {
      std::cout << adjustment << "\n";
      show(lf::get_price("000001.XSHE", "2024-03-01", "2024-03-11", "1d", {"close", "volume", "turnover"}, false,
                         true, adjustment));
    }
    // 4. 排除停牌行，用于只统计有交易的观测；没有停牌时两种设置结果相同。
    show(lf::get_price("000001.XSHE", "2024-03-01", "2024-03-11", "1d", {"close"}, /*skip_suspended=*/true));
    // 5. 美股：代码自带市场，不需要 market 参数；与 A 股、指数混在一批也可以。
    show(lf::get_price({"AAPL.US", "NVDA.US"}, "2026-03-02", "2026-03-11", "1d",
                       {"open", "high", "low", "close", "volume"}));
    // [/get_price]

    // [get_price_coverage]
    // 最近 5 个已覆盖的交易日：先问行情上界，再从日历回溯，不能直接把今天当上界。
    // 覆盖按证券类型与场所给出：{"stock": {"XSHE": {...}, ...}, "index": {...}}。
    const lf::Json coverage = lf::get_price_coverage("cn");
    show(coverage);
    const std::string end = coverage["stock"]["XSHE"]["end"].get<std::string>();
    const auto dates = lf::get_n_trading_dates_until(end, 5, "cn");
    show(lf::get_price("000001.XSHE", dates.front(), dates.back(), "1d", {"close"}));
    // [/get_price_coverage]
  });
}
