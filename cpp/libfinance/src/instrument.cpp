// Python: libfinance/api/instrument.py.
#include "libfinance/instrument.hpp"

#include <algorithm>
#include <cctype>
#include <map>

#include "internal.hpp"

namespace libfinance {

namespace {

//: The types the server's all_instruments knows, and their historical aliases.
const std::vector<std::string> kValidTypes = {"CS", "INDX"};
const std::map<std::string, std::string> kTypeAliases = {{"STOCK", "CS"}, {"INDEX", "INDX"}};

//: `_normalize_types`: upper-cased, aliases resolved, checked; null for none.
Json normalize_types(const Codes& type) {
  if (!type.given()) return Json();
  Json out = Json::array();
  for (const auto& item : detail::list_of(type, "type")) {
    std::string upper = item;
    std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char c) { return std::toupper(c); });
    auto alias = kTypeAliases.find(upper);
    if (alias != kTypeAliases.end()) upper = alias->second;
    if (std::find(kValidTypes.begin(), kValidTypes.end(), upper) == kValidTypes.end())
      throw std::invalid_argument("invalid type: '" + item + "', choose any in " + detail::py_list(kValidTypes));
    out.push_back(upper);
  }
  return out;
}

//: `_all_instruments_cached`: the whole table, by data version (get_price needs it every time).
Table all_instruments_cached(const Json& types, const Json& as_of) {
  static detail::VersionedCache<Table> cache;
  const Json key = {types, as_of};
  return cache.get(key.dump(), [&] {
    return detail::column_first(detail::call_table("all_instruments", {{"type", types}, {"as_of", as_of}}),
                                "order_book_id");
  });
}

}  // namespace

const Json& Instrument::operator[](const std::string& name) const {
  static const Json kMissing;
  auto it = fields_.find(name);
  return it == fields_.end() ? kMissing : *it;
}

std::string Instrument::text(const std::string& name) const {
  const Json& value = (*this)[name];
  return value.is_string() ? value.get<std::string>() : std::string();
}

bool Instrument::has_citics_info() const {
  const std::string code = order_book_id();
  auto ends_with = [&](const std::string& suffix) {
    return code.size() >= suffix.size() && code.compare(code.size() - suffix.size(), suffix.size(), suffix) == 0;
  };
  return type() == "CS" && (ends_with(".XSHE") || ends_with(".XSHG"));
}

Table all_instruments(const Codes& type, const std::optional<DateLike>& as_of, const std::optional<std::string>& market,
                      bool cached) {
  const Json types = normalize_types(type);
  if (cached && !market) return all_instruments_cached(types, detail::iso_or_null(as_of));
  return detail::column_first(detail::call_table("all_instruments", {{"type", types},
                                                                     {"as_of", detail::iso_or_null(as_of)},
                                                                     {"market", detail::text_or_null(market)}}),
                              "order_book_id");
}

std::vector<Instrument> instruments(const Codes& order_book_ids, const std::optional<DateLike>& as_of) {
  const std::vector<std::string> ids = detail::order_book_ids(order_book_ids);
  const Table table = detail::call_table("instruments", {{"symbols", ids}, {"as_of", detail::iso_or_null(as_of)}});
  std::map<std::string, Json> by_id;
  for (Json& row : detail::rows_of(table)) {
    const std::string id = row.value("order_book_id", "");
    by_id.emplace(id, std::move(row));
  }
  // in the order given; codes the server did not find are skipped
  std::vector<Instrument> found;
  for (const auto& id : ids) {
    auto it = by_id.find(id);
    if (it != by_id.end()) found.emplace_back(it->second);
  }
  return found;
}

namespace detail {

//: `all_cached_obid_to_type_mapping`: {order_book_id: type} as of a day (get_price classifies with it).
std::map<std::string, std::string> type_by_order_book_id(const std::optional<DateLike>& as_of) {
  const Table table = all_instruments_cached(Json(), iso_or_null(as_of));
  const auto ids = strings_of(table, "order_book_id");
  const auto types = strings_of(table, "type");
  std::map<std::string, std::string> out;
  for (size_t i = 0; i < ids.size() && i < types.size(); ++i) out.emplace(ids[i], types[i]);
  return out;
}

}  // namespace detail

}  // namespace libfinance
