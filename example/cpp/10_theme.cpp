// 主题：证券所属主题、主题成分与主题权重，THS 主题（与 example/python/10_theme.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // 证券当前所属的主题
      show(lf::get_instrument_themes({"600000.XSHG", "000001.XSHE"}, "THS"), 10);
    }

    {  // 一个主题的成分
      show_list(lf::get_theme_constituents("300008.THS"));
    }

    {  // 主题权重：由成分名单推出的等权
      show(lf::get_theme_weights("300008.THS"));
    }
  });
}
