// 因子：alpha158 与 Barra CNE5 的日频因子暴露，因子名写全名（与 example/python/13_factors.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // alpha158：库名展开为它的 158 个因子，每个因子一列
      const auto f = lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"}, {"system/alpha158"},
                                             "2026-08-27", "2026-09-10");
      std::cout << f->num_rows() << " rows x " << f->num_columns() - 2 << " factors\n";
      show(f->SelectColumns({0, 1, 2, 3, 4, 5, 6, 7}).ValueOrDie(), 0);  // order_book_id, date, 前 6 个因子
    }

    {  // Barra CNE5：42 列（10 个风格、31 个行业、COUNTRY）；风格因子在当天全部 A 股上标准化
      const auto f = lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"}, "system/barra-cne5", "2026-09-01",
                                             "2026-09-10");
      std::cout << f->num_rows() << " rows x " << f->num_columns() - 2 << " factors\n";
      show(f->SelectColumns({0, 1, 2, 3, 4, 5, 6, 7}).ValueOrDie(), 0);  // order_book_id, date, 前 6 个风格
    }
  });
}
