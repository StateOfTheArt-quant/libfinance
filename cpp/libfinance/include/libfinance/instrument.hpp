// Securities (Python: libfinance/api/instrument.py).
//
// order_book_id is the code (600000.XSHG), symbol the name -- the server's public column names.
#pragma once

#include <optional>
#include <string>
#include <vector>

#include "libfinance/types.hpp"

namespace libfinance {

//: One security's details; the fields are the all_instruments columns.
class Instrument {
 public:
  explicit Instrument(Json fields) : fields_(std::move(fields)) {}

  std::string order_book_id() const { return text("order_book_id"); }
  std::string symbol() const { return text("symbol"); }
  std::string type() const { return text("type"); }
  //: A field by column name; null when the security has no such field.
  const Json& operator[](const std::string& name) const;
  const Json& fields() const { return fields_; }
  bool has_citics_info() const;

 private:
  std::string text(const std::string& name) const;
  Json fields_;
};

//: Every security. `type`: "CS" (stock) or "INDX" (index), also "STOCK" / "INDEX", one or a list;
//: none for all. Cached by the server's data version when `market` is omitted and `cached`.
Table all_instruments(const Codes& type = {}, const std::optional<DateLike>& as_of = std::nullopt,
                      const std::optional<std::string>& market = std::nullopt, bool cached = true);

//: The securities of these codes, in the order given; unknown codes are skipped. (Python returns
//: one Instrument or None for a single code; C++ always answers a list.)
std::vector<Instrument> instruments(const Codes& order_book_ids, const std::optional<DateLike>& as_of = std::nullopt);

}  // namespace libfinance
