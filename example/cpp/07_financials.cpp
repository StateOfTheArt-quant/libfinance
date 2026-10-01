// 基本面：报告季度回答哪一期，as_of 回答当时已经知道哪一版（Python：example/python/07_financials.py）。
#include "show.hpp"

int main() {
  return run([] {
    // [get_pit_financials_ex]
    // 1. 最新可见版本：适用于今天研究历史季度，不等同于历史回测可见值。
    show(lf::get_pit_financials_ex("600000.XSHG", {"net_profit"}, "2024q1", "2024q3"));
    // 2. 固定季度，加 as_of：只使用截至 2024-11-01 已披露的信息。
    show(lf::get_pit_financials_ex("600000.XSHG", {"net_profit"}, "2024q1", "2024q3", "2024-11-01", "latest"));
    // 3. 同一个截止日，把 latest 改为 all，查看当时可见的全部修订版本。
    show(lf::get_pit_financials_ex({"600000.XSHG", "000001.XSHE"}, {"net_profit"}, "2024q1", "2024q3", "2024-11-01",
                                   "all"));
    // [/get_pit_financials_ex]

    // [get_factor]
    // 1. TTM 等衍生指标用 get_factor，原始报表项目用 get_pit_financials_ex。
    show(lf::get_factor("600000.XSHG", {"net_profit_ttm"}, "2024q1", "2024q3"));
    // 2. 多只股票、同一知识截止日，供同一回测截面的比较使用。
    show(lf::get_factor({"600000.XSHG", "000001.XSHE"}, {"net_profit_ttm"}, "2024q1", "2024q3", "2024-11-01"));
    // [/get_factor]
  });
}
