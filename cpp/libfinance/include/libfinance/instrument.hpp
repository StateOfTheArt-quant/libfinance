// The instrument catalog: stocks, indexes, industries and themes behind one instrument aggregate
// (Python: libfinance/api/instrument.py). Signatures and columns are the backend's
// (instrument.all_instruments / instrument.instruments).
//
// order_book_id is the code (600000.XSHG) and the only identifier the client sees; name is the name.
#pragma once

#include <optional>
#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: One instrument; the fields are the all_instruments columns.
class Instrument {
 public:
  explicit Instrument(Json fields) : fields_(std::move(fields)) {}

  std::string order_book_id() const { return text("order_book_id"); }
  std::string type() const { return text("type"); }
  std::string market() const { return text("market"); }
  std::string name() const { return text("name"); }
  //: A field by column name; null when the instrument has no such field.
  const Json& operator[](const std::string& name) const;
  const Json& fields() const { return fields_; }

 private:
  std::string text(const std::string& name) const;
  Json fields_;
};

//: The catalog: columns order_book_id, type, market, name, exchange, source.
//: `type`: "stock" / "index" / "industry" / "theme" (any case), one or a list; none for all.
//: `market`: "cn" / "us"; `source`: who numbers the instrument (XSHG, CSI, SW, ...), one or a list.
//: Cached by the server's data version when `market` is omitted and `cached`.
Table all_instruments(const Codes& type = {}, const std::optional<std::string>& market = std::nullopt,
                      const Codes& source = {}, const std::optional<DateLike>& as_of = std::nullopt,
                      bool cached = true);

//: The instruments of these codes, of any type, in the order given; unknown codes are skipped.
//: `last_known` also resolves a stock or index code whose listing had ended by `as_of`. (Python
//: returns one Instrument or None for a single code; C++ always answers a list.)
std::vector<Instrument> instruments(const Codes& order_book_ids, const std::optional<DateLike>& as_of = std::nullopt,
                                    bool last_known = false);

}  // namespace libfinance
