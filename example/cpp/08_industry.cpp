// 行业：证券属于哪些行业、行业包含哪些证券、成分各占多少（Python：example/python/08_industry.py）。
//
// 行业以 order_book_id（<分类代码>.<分类体系>，如 480000.SW）命名；source 是分类体系，level 是层级。
#include "show.hpp"

int main() {
  return run([] {
    // [get_instrument_industry]
    // 同一组股票在申万体系里的一级与三级行业；related_order_book_id 就是行业代码。
    for (int level : {1, 3}) show(lf::get_instrument_industry({"000001.XSHE", "600000.XSHG"}, "SW", level, "2024-06-28"));
    // [/get_instrument_industry]

    // [get_industry_constituents]
    // 反向查询：从证券的行业拿到行业代码，再取当日的成分证券。
    const lf::Table industries = lf::get_instrument_industry({"600000.XSHG"}, "SW", 1, "2024-06-28");
    if (industries && industries->num_rows() > 0) {
      const auto codes = std::static_pointer_cast<arrow::StringArray>(
          industries->GetColumnByName("related_order_book_id")->chunk(0));
      const std::string industry = codes->GetString(0);
      show(lf::get_industry_constituents(industry, "2024-06-28"));
      show(lf::get_industry_constituents(industry));  // 去掉 as_of，取已确认的最新日期
    }
    // [/get_industry_constituents]

    // [get_industry_weights]
    // 行业成分的权重；每行都带 methodology，说明权重是怎么来的。
    show(lf::get_industry_weights("480000.SW", "2024-06-28"));
    // [/get_industry_weights]
  });
}
