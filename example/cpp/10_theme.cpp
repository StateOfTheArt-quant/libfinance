// 主题（概念）：证券属于哪些主题、主题包含哪些证券、成分各占多少（Python：example/python/10_theme.py）。
//
// 主题以 order_book_id（300900.THS）命名，目录是 all_instruments(type="theme")；source 是主题定义方。
// 同花顺主题的数据从 2026-06-29 起，更早的 as_of 抛 CoverageError。
#include "show.hpp"

int main() {
  return run([] {
    // [get_instrument_themes]
    // 证券在当日所属的主题；related_order_book_id 就是主题代码。
    show(lf::get_instrument_themes({"600000.XSHG", "000001.XSHE"}, "THS"));
    // [/get_instrument_themes]

    // [get_theme_constituents]
    // 主题代码来自目录，不硬编码可能已失效的编号。
    const lf::Table themes = lf::all_instruments("theme", std::nullopt, "THS");
    show(themes);
    if (!themes || themes->num_rows() == 0) return;
    const auto codes = std::static_pointer_cast<arrow::StringArray>(themes->GetColumnByName("order_book_id")->chunk(0));
    const std::string theme = codes->GetString(0);
    show(lf::get_theme_constituents(theme));
    show(lf::get_theme_constituents(theme, "2026-07-31"));  // 那一天还没有这个主题时为 null
    // [/get_theme_constituents]

    // [get_theme_weights]
    // 同花顺主题的权重是由成分名单推出的等权（methodology=derived_equal_weight），不是供应商权重。
    show(lf::get_theme_weights(theme));
    // [/get_theme_weights]
  });
}
