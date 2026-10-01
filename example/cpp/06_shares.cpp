// 股本结构：全历史、日期截面与字段子集；所有股本字段的单位均为股（Python：example/python/06_shares.py）。
#include "show.hpp"

int main() {
  return run([] {
    // [get_shares]
    // 1. 不传日期，从首个股本事件到最后一个股本事件，返回全部字段。
    show(lf::get_shares("600000.XSHG"));
    // 2. 多只股票、指定窗口，只取发行股本与可流通股本。
    show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-01-01", "2024-06-28", {"issued_shares", "tradable_shares"}));
    // 3. 开始日等于结束日，查询单日截面；自由流通股本与可流通股本不是同一个字段。
    show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-06-28", "2024-06-28",
                        {"tradable_shares", "free_float_shares"}));
    // [/get_shares]
  });
}
