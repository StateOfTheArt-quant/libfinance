// 公司行动：日期窗口筛选事件，as_of 限制已知信息（Python：example/python/05_corporate_actions.py）。
//
// 四个函数均接受 (order_book_ids, start_date, end_date, fields, as_of)，返回事件表。
// 市场由代码推断；空表表示没有匹配事件；分拆仅支持美股代码。
#include "show.hpp"

int main() {
  return run([] {
    // [get_dividends]
    // 1. 单只证券全部分红事件。
    show(lf::get_dividends("600000.XSHG"));
    // 2. 多只证券、限定事件日期和返回字段。
    show(lf::get_dividends({"600000.XSHG", "000001.XSHE"}, "2024-01-01", "2024-06-28", {"ex_date", "cash_per_share"}));
    // 3. 同样的事件窗口，只取截至指定时点已知的信息。
    show(lf::get_dividends("600000.XSHG", "2024-01-01", "2024-06-28", {}, "2024-06-28"));
    // 4. 混合市场批量查询：代码已包含市场信息，不需要 market 参数。
    show(lf::get_dividends({"600000.XSHG", "AAPL.US"}, "2024-01-01", "2024-12-31", {"ex_date", "cash_per_share"}));
    // [/get_dividends]

    // [get_splits]
    // 拆股/送转事件用于解释股数和价格变化；ratio_from 股变为 ratio_to 股。
    show(lf::get_splits("600000.XSHG", "2020-01-01", "2024-12-31"));
    show(lf::get_splits("NVDA.US", "2024-01-01", "2024-12-31"));
    // [/get_splits]

    // [get_allotments]
    // 配股是独立事件，不应与现金分红混为一谈；缩小日期范围可能得到空表。
    show(lf::get_allotments("600000.XSHG"));
    show(lf::get_allotments("600000.XSHG", "2024-01-01", "2024-12-31"));
    // [/get_allotments]

    // [get_spinoffs]
    // 美股分拆：保留全部字段，同时查看 valuation_price/basis/source 的估值口径。
    show(lf::get_spinoffs("MMM.US", "2024-01-01", "2024-12-31"));
    // [/get_spinoffs]
  });
}
