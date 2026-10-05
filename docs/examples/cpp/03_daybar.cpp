// 日频行情：股票与指数、字段、复权方式与查询窗口（与 docs/examples/python/03_daybar.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [get_price.1] 单只股票的收盘价与成交量（默认前复权）
      show(lf::get_price("000001.XSHE", "2024-03-01", "2024-03-11", "1d", {"close", "volume"}), 0);
    }  // [/get_price.1]

    {  // [get_price.2] 股票与指数混在一批
      show(lf::get_price({"000001.XSHE", "000300.XSHG"}, "2024-03-01", "2024-03-05", "1d",
                         {"open", "high", "low", "close"}), 0);
    }  // [/get_price.2]

    {  // [get_price.3] 复权方式：不复权、前复权、后复权
      for (const char* adjust_type : {"none", "pre", "post"}) {
        std::cout << adjust_type << "\n";
        show(lf::get_price("600519.XSHG", "2024-03-01", "2024-03-05", "1d", {"close", "volume"}, false, true,
                           adjust_type), 0);
      }
    }  // [/get_price.3]

    {  // [get_price.4] 排除停牌日
      show(lf::get_price("000001.XSHE", "2024-03-01", "2024-03-11", "1d", {"close"}, true), 0);
    }  // [/get_price.4]

    {  // [get_price.5] 美股：代码自带市场
      show(lf::get_price({"AAPL.US", "NVDA.US"}, "2026-03-02", "2026-03-04", "1d", {"close", "volume"}), 0);
    }  // [/get_price.5]

    {  // [get_price_coverage.1] 行情覆盖到哪天：按证券类型与交易所给出
      show(lf::get_price_coverage("cn")["stock"]);
    }  // [/get_price_coverage.1]

    {  // [get_price_coverage.2] 最近 5 个有行情的交易日：以覆盖上界为终点
      const std::string end = lf::get_price_coverage("cn")["stock"]["XSHE"]["end"];
      const auto dates = lf::get_n_trading_dates_until(end, 5, "cn");
      show(lf::get_price("000001.XSHE", dates.front(), dates.back(), "1d", {"close"}), 0);
    }  // [/get_price_coverage.2]
  });
}
