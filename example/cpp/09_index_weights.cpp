// 指数成分：最新锚点与指定交易日的权重（Python：example/python/09_index_weights.py）。
//
// 返回 index_code/date/order_book_id/weight；权重是比例，不是百分数。
#include <arrow/compute/api.h>

#include "show.hpp"

int main() {
  return run([] {
    // [get_index_weights]
    // 1. 省略 date，查询最新一期锚点。
    show(lf::get_index_weights("000300.XSHG"));
    // 2. 指定交易日：非锚点日由最近的历史锚点按复权收益率推算。
    const lf::Table weights = lf::get_index_weights("000300.XSHG", "2024-06-28");
    show(weights);
    // 检查同一指数、同一天的权重和
    const auto sum = arrow::compute::Sum(weights->GetColumnByName("weight"));
    if (sum.ok()) std::cout << sum->scalar()->ToString() << "\n";
    // 3. 保持日期不变，改变指数，构造另一组研究样本。
    show(lf::get_index_weights("000905.XSHG", "2024-06-28"));
    // [/get_index_weights]
  });
}
