// 指数：证券所属指数、指数成分与指数权重（与 docs/examples/python/09_index.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [get_instrument_indices.1] 一只 A 股、一只美股所属的指数
      show(lf::get_instrument_indices({"600000.XSHG", "AAPL.US"}, std::nullopt, "2024-06-28"), 10);
    }  // [/get_instrument_indices.1]

    {  // [get_instrument_indices.2] 只看中证指数公司（CSI）发布的指数
      show(lf::get_instrument_indices("600000.XSHG", "CSI", "2024-06-28"), 0);
    }  // [/get_instrument_indices.2]

    {  // [get_index_constituents.1] 沪深 300 在 2024-06-28 的成分
      show_list(lf::get_index_constituents("000300.XSHG", "2024-06-28"));
    }  // [/get_index_constituents.1]

    {  // [get_index_constituents.2] 省略 as_of：已确认的最新成分
      show_list(lf::get_index_constituents("SPX.US"));
    }  // [/get_index_constituents.2]

    {  // [get_index_weights.1] 成分权重与 methodology；非月末日按复权收益率漂移
      const auto weights = lf::get_index_weights("000300.XSHG", "2024-06-28");
      show(weights);
      std::cout << column_sum(weights, "weight") << "\n";
    }  // [/get_index_weights.1]
  });
}
