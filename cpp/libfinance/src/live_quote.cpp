// Python: libfinance/api/live_quote.py. This is the RPC snapshot; continuous pushes are the quote
// gateway's (a separate path).
#include "libfinance/live_quote.hpp"

#include "internal.hpp"

namespace libfinance {

Json get_last_quotes(const std::vector<std::string>& order_book_ids) {
  Json quotes = detail::call("get_last_quotes", {{"order_book_ids", order_book_ids}});
  // a missing snapshot stays null; inside a snapshot, missing values are dropped rather than kept
  // as nulls, so arithmetic on a quote never meets one
  for (auto& [code, quote] : quotes.items()) {
    if (!quote.is_object()) continue;
    for (auto field = quote.begin(); field != quote.end();)
      field = field->is_null() ? quote.erase(field) : std::next(field);
  }
  return quotes;
}

}  // namespace libfinance
