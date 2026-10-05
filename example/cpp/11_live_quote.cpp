// 实时快照：一次查询多只证券的最新行情（与 example/python/11_live_quote.py 一一对应）。
#include "show.hpp"

int main() {
  return run([] {
    {  // 一次查询多只证券；还没有快照的为 None
      const lf::Json quotes = lf::get_last_quotes({"600000.XSHG", "000001.XSHE"});
      for (const auto& [code, quote] : quotes.items())
        std::cout << code << " " << (quote.is_null() ? "None" : quote.value("last_price", lf::Json()).dump()) << "\n";
    }
  });
}
