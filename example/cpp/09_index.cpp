// 指数：证券属于哪些指数、指数包含哪些证券、成分各占多少（Python：example/python/09_index.py）。
//
// 指数以 order_book_id（000300.XSHG、SPX.US）命名；source 是指数发布机构；权重是比例，不是百分数。
#include <arrow/compute/api.h>

#include "show.hpp"

int main() {
  return run([] {
    // [get_instrument_indices]
    // 一只 A 股、一只美股在当日所属的指数；related_order_book_id 就是指数代码。
    show(lf::get_instrument_indices({"600000.XSHG", "AAPL.US"}, std::nullopt, "2024-06-28"));
    // 只看中证指数公司发布的指数。
    show(lf::get_instrument_indices("600000.XSHG", "CSI", "2024-06-28"));
    // [/get_instrument_indices]

    // [get_index_constituents]
    // 沪深300 在 2024-06-28 的成分；去掉 as_of 取已确认的最新日期。
    show(lf::get_index_constituents("000300.XSHG", "2024-06-28"));
    show(lf::get_index_constituents("SPX.US"));
    // [/get_index_constituents]

    // [get_index_weights]
    // 同一指数、同一天的权重；每行都带 methodology，说明权重是怎么来的。
    const lf::Table weights = lf::get_index_weights("000300.XSHG", "2024-06-28");
    show(weights);
    const auto sum = arrow::compute::Sum(weights->GetColumnByName("weight"));  // 检查权重和
    if (sum.ok()) std::cout << sum->scalar()->ToString() << "\n";
    // [/get_index_weights]
  });
}
