// Python: libfinance/api/concept_components.py.
#include "libfinance/concept_components.hpp"

#include <set>

#include "internal.hpp"

namespace libfinance {

namespace {

//: `_warn_unknown_concepts`: the server answers an id it never saw with no rows, which looks like a
//: concept with no members today. The metadata is cached, so this costs no round trip; when it
//: cannot be had the query goes ahead.
void warn_unknown_concepts(const std::vector<std::string>& concept_ids, const std::string& source) {
  std::set<std::string> known;
  try {
    for (const auto& id : detail::strings_of(get_concept_meta(source), "concept_id")) known.insert(id);
  } catch (const std::exception&) {
    return;
  }
  if (known.empty()) return;
  std::vector<std::string> missing;
  for (const auto& id : concept_ids)
    if (!known.count(id)) missing.push_back(id);
  if (missing.empty()) return;
  std::string listed;
  for (size_t i = 0; i < missing.size() && i < 5; ++i) listed += (i ? ", " : "") + missing[i];
  detail::warn("未知的 concept_id: " + listed + "（source='" + source + "'）。用 get_concept_meta() 查可用的概念。");
}

}  // namespace

Table get_concept_meta(const std::string& source, const Codes& fields, const std::optional<std::string>& market) {
  static detail::VersionedCache<Table> cache;
  const Json args = {{"source", source}, {"fields", detail::as_given(fields)}, {"market", detail::text_or_null(market)}};
  return cache.get(args.dump(), [&] { return detail::call_table("get_concept_meta", args); });
}

Table get_concept_weights(const std::vector<std::string>& concept_ids, const std::optional<DateLike>& as_of,
                          const std::string& source, const std::optional<std::string>& market) {
  warn_unknown_concepts(concept_ids, source);
  return detail::call_table("get_concept_weights", {{"concept_ids", concept_ids},
                                                    {"source", source},
                                                    {"market", detail::text_or_null(market)},
                                                    {"as_of", detail::iso_or_null(as_of)}});
}

}  // namespace libfinance
