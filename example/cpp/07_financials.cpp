// 基本面：报告季度回答哪一期，as_of 回答当时已经知道哪一版；衍生指标按交易日给出
// （Python：example/python/07_financials.py）。
#include "show.hpp"

int main() {
  return run([] {
    // [get_pit_financials_ex]
    // 1. 最新可见版本：适用于今天研究历史季度，不等同于历史回测可见值。
    show(lf::get_pit_financials_ex("600000.XSHG", {"total_operating_revenue", "net_income_parent"}, "2024q1",
                                   "2024q3"));
    // 2. 固定季度，加 as_of：只使用截至 2024-11-01 已披露的信息。
    show(lf::get_pit_financials_ex("600000.XSHG", {"net_income_parent"}, "2024q1", "2024q3", "2024-11-01", "latest"));
    // 3. 同一个截止日，把 latest 改为 all，查看当时可见的全部修订版本；CN 与 US 同一套字段。
    show(lf::get_pit_financials_ex({"600000.XSHG", "AAPL.US"}, {"net_income_parent", "assets"}, "2024q1", "2024q3",
                                   "2024-11-01", "all"));
    // [/get_pit_financials_ex]

    // [get_financial_metrics]
    // 1. 每个交易日的值来自那天收盘后可见的最新报告：在公告日跳变，其间持平。
    show(lf::get_financial_metrics("600519.XSHG", {"roe_lf", "revenue_ttm"}, "2024-10-28", "2024-11-01"));
    // 2. 多只股票、CN 与 US 同一套公式；省略日期取最近一个交易日。
    show(lf::get_financial_metrics({"600519.XSHG", "AAPL.US"}, {"net_profit_growth_lyr", "debt_to_assets_lf"}));
    // [/get_financial_metrics]
  });
}
