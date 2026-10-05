// 股本：发行股本、可流通股本与自由流通股本的逐日面板（与 example/python/06_shares.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // 一只股票的全部股本字段
      show(lf::get_shares("600000.XSHG"));
    }

    {  // 多只股票、限定窗口与字段
      show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-06-24", "2024-06-28",
                          {"issued_shares", "tradable_shares"}), 0);
    }

    {  // 单日截面：开始日等于结束日
      show(lf::get_shares({"000001.XSHE", "600000.XSHG"}, "2024-06-28", "2024-06-28",
                          {"tradable_shares", "free_float_shares"}), 0);
    }
  });
}
