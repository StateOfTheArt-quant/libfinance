// 公司行动：分红、拆股与送转、配股、分拆（与 example/python/05_corporate_actions.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // 一只股票的全部分红事件
      show(lf::get_dividends("600000.XSHG"));
    }

    {  // 多只股票、限定日期与字段
      show(lf::get_dividends({"600000.XSHG", "000001.XSHE"}, "2024-01-01", "2024-06-28", {"ex_date", "cash_per_share"}), 0);
    }

    {  // as_of：只看截至那天已知的事件
      show(lf::get_dividends("600000.XSHG", "2024-01-01", "2024-06-28", {"ex_date", "cash_per_share"}, "2024-06-28"), 0);
    }

    {  // A 股与美股混在一批
      show(lf::get_dividends({"600000.XSHG", "AAPL.US"}, "2024-01-01", "2024-12-31", {"ex_date", "cash_per_share"}), 0);
    }

    {  // 一只 A 股的全部拆股事件：ratio_from 股变为 ratio_to 股
      show(lf::get_splits("600000.XSHG"), 0);
    }

    {  // 拆股（美股）
      show(lf::get_splits("NVDA.US", "2024-01-01", "2024-12-31"), 0);
    }

    {  // 一只股票的配股事件
      show(lf::get_allotments("600000.XSHG"), 0);
    }

    {  // 窗口内没有配股时返回空表
      show(lf::get_allotments("600000.XSHG", "2024-01-01", "2024-12-31"), 0);
    }

    {  // 美股分拆及其估值口径
      show(lf::get_spinoffs("MMM.US", "2024-01-01", "2024-12-31"), 0);
    }
  });
}
