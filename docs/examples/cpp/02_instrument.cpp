// 证券目录：股票、指数、行业、主题在同一个目录里；先确定范围，再按代码查询（与 docs/examples/python/02_instrument.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // [all_instruments.1] 目录全貌：按类型与市场计数
      count_by(lf::all_instruments(), "type", "market");
    }  // [/all_instruments.1]

    {  // [all_instruments.2] A 股股票：source 是上市交易所
      show(lf::all_instruments("stock", "cn"));
    }  // [/all_instruments.2]

    {  // [all_instruments.3] 中证指数公司（CSI）发布的指数
      show(lf::all_instruments("index", std::nullopt, "CSI"));
    }  // [/all_instruments.3]

    {  // [all_instruments.4] 申万（SW）行业：source 是分类体系
      show(lf::all_instruments("industry", std::nullopt, "SW"));
    }  // [/all_instruments.4]

    {  // [all_instruments.5] THS 主题，仅 A 股
      show(lf::all_instruments("theme"));
    }  // [/all_instruments.5]

    {  // [all_instruments.6] 一次取几种类型：type 给列表
      count_by(lf::all_instruments({"index", "industry"}, "cn"), "type", "source");
    }  // [/all_instruments.6]

    {  // [all_instruments.7] 历史时点：申万 2021 年改版前后的行业数
      const auto before = lf::all_instruments("industry", std::nullopt, "SW", "2020-01-02");
      const auto after = lf::all_instruments("industry", std::nullopt, "SW", "2022-04-15");
      std::cout << before->num_rows() << " " << after->num_rows() << "\n";
    }  // [/all_instruments.7]

    {  // [instruments.1] 单个代码：返回一个证券，查不到为 None
      for (const auto& stock : lf::instruments("000001.XSHE"))
        std::cout << stock.order_book_id() << " " << stock.name() << " " << stock.type() << " "
                  << stock.permanent_id() << "\n";
    }  // [/instruments.1]

    {  // [instruments.2] 一个列表混合四种类型、两个市场：类型由代码决定
      for (const auto& item :
           lf::instruments({"000001.XSHE", "000300.XSHG", "480000.SW", "300008.THS", "AAPL.US", "45.GICS"}))
        std::cout << item.order_book_id() << " " << item.type() << " " << item.market() << " " << item.name() << "\n";
    }  // [/instruments.2]

    {  // [instruments.3] as_of：按当日有效的身份解析（Meta 在 2022 年仍叫 FB.US）
      for (const auto& item : lf::instruments({"FB.US", "000300.XSHG"}, "2022-04-15"))
        std::cout << item.order_book_id() << " " << item.name() << "\n";
    }  // [/instruments.3]

    {  // [instruments.4] last_known：已退市的代码按最后一次的身份解析
      std::cout << lf::instruments("ATVI.US").size() << "\n";
      std::cout << lf::instruments("ATVI.US", std::nullopt, true).front().name() << "\n";
    }  // [/instruments.4]
  });
}
