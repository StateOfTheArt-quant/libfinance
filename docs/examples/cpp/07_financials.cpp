// 财务：季度报表的 point-in-time 视图与逐交易日的财务衍生指标（与 docs/examples/python/07_financials.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [get_pit_financials_ex.1] 最新可见版本
      show(lf::get_pit_financials_ex("600000.XSHG", {"total_operating_revenue", "net_income_parent"}, "2024q1",
                                     "2024q3"), 0);
    }  // [/get_pit_financials_ex.1]

    {  // [get_pit_financials_ex.2] as_of：只用截至那天已披露的信息
      show(lf::get_pit_financials_ex("600000.XSHG", {"net_income_parent"}, "2024q1", "2024q3", "2024-11-01", "latest"), 0);
    }  // [/get_pit_financials_ex.2]

    {  // [get_pit_financials_ex.3] statements="all"：当时可见的全部修订版本
      show(lf::get_pit_financials_ex({"600000.XSHG", "AAPL.US"}, {"net_income_parent"}, "2024q1", "2024q3",
                                     "2024-11-01", "all"), 0);
    }  // [/get_pit_financials_ex.3]

    {  // [get_financial_metrics.1] 逐交易日的指标：在公告日跳变，其间持平
      show(lf::get_financial_metrics("600519.XSHG", {"roe_lf", "revenue_ttm"}, "2024-10-28", "2024-11-01"), 0);
    }  // [/get_financial_metrics.1]

    {  // [get_financial_metrics.2] A 股与美股同一套公式；省略日期取最近一个交易日
      show(lf::get_financial_metrics({"600519.XSHG", "AAPL.US"}, {"net_profit_growth_lyr", "debt_to_assets_lf"}), 0);
    }  // [/get_financial_metrics.2]
  });
}
