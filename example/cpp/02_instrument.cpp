// 证券目录：股票、指数、行业、主题在同一个目录里，先确定范围，再按代码查询
// （Python：example/python/02_instrument.py）。
//
// all_instruments(type, market, source, as_of, cached) -> Table
//   type：stock / index / industry / theme；market：cn / us；source：编号机构；as_of：历史视图。
// instruments(order_book_ids, as_of, last_known) -> std::vector<Instrument>
//   类型由代码本身决定；C++ 总是返回列表，代码可混合市场与类型。
#include "show.hpp"

int main() {
  return run([] {
    // [all_instruments]
    // 1. 目录里有什么？每行一只证券：order_book_id、permanent_id、type、market、name、exchange、source。
    show(lf::all_instruments());
    // 2. 只看 A 股股票：改变 type 与 market，返回形状不变。
    show(lf::all_instruments("stock", "cn"));
    // 3. 中证指数公司发布的指数：source 是编号机构。
    show(lf::all_instruments("index", std::nullopt, "CSI"));
    // 4. 历史时点的股票：as_of 决定身份快照，不表示当日一定有成交。
    show(lf::all_instruments("stock", "cn", {}, "2025-09-18"));
    // 5. 美股：exchange 是上市的交易所。
    show(lf::all_instruments("stock", "us", {}, "2025-06-16"));
    // [/all_instruments]

    // [instruments]
    // 1. 单个代码；查不到时列表为空。
    for (const auto& stock : lf::instruments("000001.XSHE"))
      std::cout << stock.order_book_id() << " " << stock.name() << " " << stock.type() << " " << stock.permanent_id()
                << "\n";
    // 2. 股票与指数、中美市场可以混在一起；按输入顺序返回，跳过查不到的代码。
    show(lf::instruments({"AAPL.US", "000001.XSHE", "000300.XSHG"}));
    // 3. 同样的列表，增加 as_of，按当日有效的代码解析。
    show(lf::instruments({"000001.XSHE", "000300.XSHG"}, "2022-04-15"));
    // 4. 已退市的代码：last_known 按它最后一次的证券解析；Meta 在 2022-04-15 使用 FB.US。
    show(lf::instruments({"FB.US", "NVDA.US"}, "2022-04-15"));
    show(lf::instruments("FB.US", std::nullopt, /*last_known=*/true));
    // [/instruments]
  });
}
