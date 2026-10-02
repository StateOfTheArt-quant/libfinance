// 证券目录：股票、指数、行业、主题在同一个目录里，先确定范围，再按代码查询
// （Python：example/python/02_instrument.py）。
//
// all_instruments(type, market, source, as_of, cached) -> Table
//   type：stock / index / industry / theme，或它们的列表；market：cn / us；source：编号机构——
//   股票是交易所，指数是发布机构，行业是分类体系，主题是主题目录；as_of：历史视图。
// instruments(order_book_ids, as_of, last_known) -> std::vector<Instrument>
//   类型由代码本身决定；C++ 总是返回列表，代码可混合市场与类型。
//
// 股票、指数与申万行业有历史；美国行业分类与主题目前只有当前快照。
#include <map>
#include <utility>

#include "show.hpp"

namespace {

//: Python 的 frame.groupby([a, b]).size()：按两列计数，任一列为空的行不计（与 pandas 相同）。
void count_by(const lf::Table& table, const std::string& a, const std::string& b) {
  std::map<std::pair<std::string, std::string>, int64_t> counts;
  const auto left = table->GetColumnByName(a), right = table->GetColumnByName(b);
  for (int64_t i = 0; i < table->num_rows(); ++i) {
    const auto x = left->GetScalar(i).ValueOrDie(), y = right->GetScalar(i).ValueOrDie();
    if (x->is_valid && y->is_valid) ++counts[{x->ToString(), y->ToString()}];
  }
  for (const auto& [key, n] : counts) std::cout << key.first << "  " << key.second << "  " << n << "\n";
}

}  // namespace

int main() {
  return run([] {
    // [all_instruments]
    // 1. 目录里有什么？每行一只证券：order_book_id、permanent_id、type、market、name、exchange、source。
    //    四种类型在同一张表里，按 type 与 market 计数看全貌。
    count_by(lf::all_instruments(), "type", "market");
    // 2. 股票：source 与 exchange 是上市的交易所。
    show(lf::all_instruments("stock", "cn"));
    // 3. 指数：source 是指数发布机构，如中证指数公司（CSI）、标普道琼斯（SPDJI）。
    show(lf::all_instruments("index", std::nullopt, "CSI"));
    show(lf::all_instruments("index", "us"), 0);
    // 4. 行业：source 是分类体系。A 股用申万（SW），美股有 GICS、ICB、NAICS、SIC 四套。
    show(lf::all_instruments("industry", std::nullopt, "SW"));
    show(lf::all_instruments("industry", std::nullopt, "GICS"));
    // 5. 主题：同花顺概念（THS），仅 A 股。
    show(lf::all_instruments("theme"));
    // 6. 几种类型一起：type 给列表。
    count_by(lf::all_instruments(std::vector<std::string>{"index", "industry"}, "cn"), "type", "source");
    // 7. 历史时点：as_of 决定身份快照，不表示当日一定有成交。
    //    申万 2021 年改版前后行业数不同；股票的 source 就是交易所，可以只看纳斯达克。
    std::cout << lf::all_instruments("industry", std::nullopt, "SW", "2020-01-02")->num_rows() << " "
              << lf::all_instruments("industry", std::nullopt, "SW", "2022-04-15")->num_rows() << "\n";
    show(lf::all_instruments("stock", "us", "XNAS", "2025-06-16"));
    // [/all_instruments]

    // [instruments]
    // 1. 单个代码；查不到时列表为空。
    for (const auto& stock : lf::instruments("000001.XSHE"))
      std::cout << stock.order_book_id() << " " << stock.name() << " " << stock.type() << " " << stock.permanent_id()
                << "\n";
    // 2. 一个列表里四种类型、两个市场都可以：类型由代码决定，按输入顺序返回，跳过查不到的代码。
    for (const auto& item : lf::instruments({"000001.XSHE", "000300.XSHG", "480000.SW", "300008.THS", "AAPL.US",
                                             "SPX.US", "45.GICS"}))
      std::cout << item.order_book_id() << " " << item.type() << " " << item.market() << " "
                << item.fields().value("source", "") << " " << item.name() << "\n";
    // 3. 增加 as_of，按当日有效的代码解析；股票、指数与申万行业都有历史。
    for (const auto& item : lf::instruments({"000001.XSHE", "000300.XSHG", "480000.SW", "SPX.US"}, "2022-04-15"))
      std::cout << item.order_book_id() << " " << item.type() << " " << item.name() << "\n";
    // 4. 代码随时间变化：Meta 在 2022-04-15 使用 FB.US。已退市的代码当前查不到，last_known 按它
    //    最后一次的证券解析：ATVI.US 在 2023-10 被微软收购后退市。
    for (const auto& item : lf::instruments({"FB.US", "NVDA.US"}, "2022-04-15")) std::cout << item.name() << "\n";
    std::cout << lf::instruments("ATVI.US").size() << " "
              << lf::instruments("ATVI.US", std::nullopt, /*last_known=*/true).front().name() << "\n";
    // [/instruments]
  });
}
