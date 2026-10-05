// 行业：证券所属行业、行业成分与行业权重（与 docs/examples/python/08_industry.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [get_instrument_industry.1] 申万一级行业
      show(lf::get_instrument_industry({"000001.XSHE", "600000.XSHG"}, "SW", 1, "2024-06-28"), 0);
    }  // [/get_instrument_industry.1]

    {  // [get_instrument_industry.2] 省略 source 与 level：全部分类体系、全部层级
      show(lf::get_instrument_industry("600000.XSHG", std::nullopt, std::nullopt, "2024-06-28"), 0);
    }  // [/get_instrument_industry.2]

    {  // [get_industry_constituents.1] 申万银行业（480000.SW）的成分
      show_list(lf::get_industry_constituents("480000.SW", "2024-06-28"));
    }  // [/get_industry_constituents.1]

    {  // [get_industry_weights.1] 行业成分的权重与 methodology
      show(lf::get_industry_weights("480000.SW", "2024-06-28"));
    }  // [/get_industry_weights.1]
  });
}
