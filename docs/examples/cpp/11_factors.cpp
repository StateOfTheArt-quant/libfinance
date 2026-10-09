// 因子：qlib、alpha158 与 Barra CNE5（factors-daybar），因子名写全名（与 docs/examples/python/11_factors.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [list_factor_libraries.1] 因子库一览
      show(lf::list_factor_libraries(), 0);
    }  // [/list_factor_libraries.1]

    {  // [list_factors.1] 一个库里的因子全名
      const auto names = lf::list_factors("system/barra-cne5");
      show(lf::Json(std::vector<std::string>(names.begin(), names.begin() + std::min<size_t>(12, names.size()))));
    }  // [/list_factors.1]

    {  // [get_factor_exposure.1] Barra CNE5 风格因子：库名展开为 42 列（10 个风格、31 个行业、COUNTRY）
      const auto f = lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"}, "system/barra-cne5", "2026-09-07", "2026-09-10");
      std::cout << f->num_rows() << " rows x " << f->num_columns() - 2 << " factors\n";
      show(f->SelectColumns({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}).ValueOrDie(), 0);  // order_book_id, date, 10 styles
    }  // [/get_factor_exposure.1]

    {  // [get_factor_exposure.2] 原始描述符与标准化后的风格因子混在一次请求里
      show(lf::get_factor_exposure({"600000.XSHG", "600519.XSHG"},
                                   {"system/barra-cne5-descriptor/LNCAP", "system/barra-cne5/SIZE", "system/barra-cne5/BANKS"},
                                   "2026-09-10", "2026-09-10"), 0);
    }  // [/get_factor_exposure.2]

    {  // [get_factor_exposure.3] universe：截面因子在给定的代码上重新标准化，时序因子不变
      const lf::Codes banks = {"600000.XSHG", "000001.XSHE", "601398.XSHG", "601288.XSHG", "600036.XSHG"};
      show(lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"},
                                   {"system/barra-cne5/SIZE", "system/barra-cne5-descriptor/LNCAP"}, "2026-09-10",
                                   "2026-09-10", banks), 0);
    }  // [/get_factor_exposure.3]

    {  // [get_factor_exposure.4] alpha158：当天的截面
      show(lf::get_factor_exposure({"600000.XSHG", "000001.XSHE", "600519.XSHG"},
                                   {"system/alpha158/KMID", "system/alpha158/ROC5", "system/alpha158/STD20"}, "2026-09-10",
                                   "2026-09-10"), 0);
    }  // [/get_factor_exposure.4]
  });
}
