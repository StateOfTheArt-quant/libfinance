// 实时快照：一次调用取当前最新报价（Python：example/python/11_live_quote.py）。持续推送见
// 12_live_subscription.cpp。
//
// get_last_quotes(order_book_ids) -> {代码: 报价或 null}，快照不是历史分钟线。
#include "show.hpp"

int main() {
  return run([] {
    // [get_last_quotes]
    // 1. 单只证券也使用列表。
    show(lf::get_last_quotes({"600000.XSHG"}));
    // 2. 一次查询多只证券，减少逐只请求。
    for (const auto& [code, quote] : lf::get_last_quotes({"600000.XSHG", "000001.XSHE"}).items()) {
      if (quote.is_null()) std::cout << code << " 暂无快照\n";
      else std::cout << code << " " << quote.value("last_price", lf::Json()) << " " << quote.value("volume", lf::Json()) << "\n";
    }
    // [/get_last_quotes]
  });
}
