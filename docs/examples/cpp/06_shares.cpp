// 股本：发行股本、可流通股本与自由流通股本的逐日面板（与 docs/examples/python/06_shares.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [get_shares.1] 一只股票的全部股本字段
      show(lf::get_shares("600000.XSHG"));
    }  // [/get_shares.1]

    {  // [get_shares.2] 多只股票、限定窗口与字段
      show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-06-24", "2024-06-28",
                          {"issued_shares", "tradable_shares"}), 0);
    }  // [/get_shares.2]

    {  // [get_shares.3] 单日截面：开始日等于结束日
      show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-06-28", "2024-06-28",
                          {"tradable_shares", "free_float_shares"}), 0);
    }  // [/get_shares.3]
  });
}
