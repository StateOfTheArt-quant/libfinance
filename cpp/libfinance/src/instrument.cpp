// Python: libfinance/api/instrument.py.
#include "libfinance/instrument.hpp"

#include <algorithm>
#include <cctype>
#include <map>

#include "internal.hpp"

namespace libfinance {

namespace {

//: The types the backend's instrument knows.
const std::vector<std::string> kValidTypes = {"stock", "index", "industry", "theme"};

//: `_normalize_types`: lower-cased and checked; null for none.
Json normalize_types(const Codes& type) {
  if (!type.given()) return Json();
  Json out = Json::array();
  for (const auto& item : detail::list_of(type, "type")) {
    std::string lower = item;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return std::tolower(c); });
    if (std::find(kValidTypes.begin(), kValidTypes.end(), lower) == kValidTypes.end())
      throw std::invalid_argument("invalid type: '" + item + "', choose any in " + detail::py_list(kValidTypes));
    out.push_back(lower);
  }
  return out;
}

Json optional_list(const Codes& values, const std::string& name) {
  return values.given() ? Json(detail::list_of(values, name)) : Json();
}

//: `_all_instruments_cached`: the whole catalog, by data version.
Table all_instruments_cached(const Json& types, const Json& sources, const Json& as_of) {
  static detail::VersionedCache<Table> cache;
  const Json key = {types, sources, as_of};
  return cache.get(key.dump(), [&] {
    return detail::column_first(
        detail::call_table("all_instruments", {{"type", types}, {"source", sources}, {"as_of", as_of}}),
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

Table all_instruments(const Codes& type, const std::optional<std::string>& market, const Codes& source,
                      const std::optional<DateLike>& as_of, bool cached) {
  const Json types = normalize_types(type), sources = optional_list(source, "source");
  if (cached && !market) return all_instruments_cached(types, sources, detail::iso_or_null(as_of));
  return detail::column_first(detail::call_table("all_instruments", {{"type", types},
                                                                     {"market", detail::text_or_null(market)},
                                                                     {"source", sources},
                                                                     {"as_of", detail::iso_or_null(as_of)}}),
                              "order_book_id");
}

std::vector<Instrument> instruments(const Codes& order_book_ids, const std::optional<DateLike>& as_of,
                                    bool last_known) {
  const std::vector<std::string> ids = detail::order_book_ids(order_book_ids);
  const Json found = detail::call("instruments", {{"order_book_ids", ids},
                                                  {"as_of", detail::iso_or_null(as_of)},
                                                  {"last_known", last_known}});
  std::map<std::string, Json> by_id;
  if (found.is_array())
    for (const Json& item : found)
      if (item.is_object()) by_id.emplace(item.value("order_book_id", ""), item);
  // in the order given; codes the server did not find are skipped
  std::vector<Instrument> out;
  for (const auto& id : ids) {
    auto it = by_id.find(id);
    if (it != by_id.end()) out.emplace_back(it->second);
  }
  return out;
}

}  // namespace libfinance
