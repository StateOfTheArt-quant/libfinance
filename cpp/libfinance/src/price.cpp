// Python: libfinance/api/get_price.py (and warn_if_clamped from libfinance/utils/cache.py).
#include "libfinance/price.hpp"

#include <algorithm>

#include <arrow/api.h>
#include <arrow/compute/api.h>

#include "internal.hpp"

namespace libfinance {

namespace {

//: What daybar publishes.
const std::vector<std::string> kFrequencies = {"1d"};
const std::vector<std::string> kAdjustTypes = {"pre", "post", "none"};
const std::vector<std::string> kTypes = {"stock", "index"};

bool contains(const std::vector<std::string>& values, const std::string& value) {
  return std::find(values.begin(), values.end(), value) != values.end();
}

void check(const arrow::Status& status) {
  if (!status.ok()) throw std::invalid_argument("libfinance: " + status.ToString());
}

//: The fields asked for, each once (a repeat warns); null for all of them. daybar checks the names.
Json fields_argument(const Codes& fields) {
  if (!fields.given()) return Json();
  std::vector<std::string> asked = detail::list_of(fields, "fields"), once, repeated;
  for (const auto& name : asked) {
    if (!contains(once, name)) once.push_back(name);
    else if (!contains(repeated, name)) repeated.push_back(name);
  }
  if (!repeated.empty()) detail::warn("duplicated fields: " + detail::py_list(repeated));
  return once;
}

// ---------------------------------------------------------------- warnings before the call

//: `_warn_beyond_coverage`: an end_date past the bars is refused by the server; say why first.
void warn_beyond_coverage(const std::string& end_date) {
  std::string latest;
  try {
    for (const char* market : {"cn", "us"})
      for (const auto& [type, venues] : get_price_coverage(market).items())
        for (const auto& [venue, entry] : venues.items()) {
          const Json end = entry.value("end", Json());
          if (end.is_string() && end.get<std::string>() > latest) latest = end.get<std::string>();
        }
  } catch (const std::exception&) {
    return;
  }
  if (latest.empty() || end_date <= latest) return;
  detail::warn("get_price: end_date=" + end_date + " 超出行情覆盖（最新已收盘交易日 " + latest +
               "）。服务端会拒绝这个区间——数据还没到不等于那天没交易。用 get_price_coverage() 查上界。");
}

// ---------------------------------------------------------------- the answer

//: `_to_panel`: daybar's flat table (order_book_id, session_date, fields...) with
//: order_book_id and datetime (session_date) first, sorted by both. A shape it does not know is
//: returned as it came.
Table to_panel(const Table& bars) {
  if (!bars || !bars->GetColumnByName("order_book_id") || !bars->GetColumnByName("session_date")) return bars;
  Table table = detail::column_first(bars, "order_book_id");

  // datetime: session_date as a timestamp (pandas' datetime64), right after order_book_id
  const int date_index = table->schema()->GetFieldIndex("session_date");
  auto moment = arrow::compute::Cast(table->column(date_index), arrow::timestamp(arrow::TimeUnit::MILLI));
  check(moment.status());
  auto without = table->RemoveColumn(date_index);
  check(without.status());
  auto with = (*without)->AddColumn(1, arrow::field("datetime", arrow::timestamp(arrow::TimeUnit::MILLI)),
                                    moment->chunked_array());
  check(with.status());
  table = *with;

  const arrow::compute::SortOptions order(
      {arrow::compute::SortKey("order_book_id"), arrow::compute::SortKey("datetime")});
  auto indices = arrow::compute::SortIndices(arrow::Datum(table), order);
  check(indices.status());
  auto sorted = arrow::compute::Take(table, *indices);
  check(sorted.status());
  return sorted->table();
}

}  // namespace

Table get_price(const Codes& order_book_ids, const DateLike& start_date, const DateLike& end_date,
                const std::string& frequency, const Codes& fields, bool skip_suspended, bool include_now,
                const std::string& adjust_type, const std::optional<DateLike>& adjust_orig) {
  std::vector<std::string> ids;
  for (const auto& code : detail::order_book_ids(order_book_ids))
    if (!contains(ids, code)) ids.push_back(code);
  detail::check_items_in({frequency}, kFrequencies, "frequency");
  detail::check_items_in({adjust_type}, kAdjustTypes, "adjust_type");
  const std::string start = start_date.iso(), end = end_date.iso();
  if (start > end) throw std::invalid_argument("start_date must not be after end_date");
  detail::warn_if_clamped("get_price", start);
  warn_beyond_coverage(end);

  // daybar routes the codes (stocks and indexes alike) by instrument as of end_date
  const Table bars = detail::call_table("get_price", {{"order_book_ids", ids},
                                                     {"start_date", start},
                                                     {"end_date", end},
                                                     {"frequency", frequency},
                                                     {"fields", fields_argument(fields)},
                                                     {"skip_suspended", skip_suspended},
                                                     {"include_now", include_now},
                                                     {"adjust_type", adjust_type},
                                                     {"adjust_orig", detail::iso_or_null(adjust_orig)}});
  return to_panel(bars);
}

Json get_price_coverage(const std::string& market) {
  static detail::VersionedCache<Json> cache;
  std::string wanted = market;
  std::transform(wanted.begin(), wanted.end(), wanted.begin(), [](unsigned char c) { return std::toupper(c); });
  return cache.get(wanted, [&] {
    const Json coverage = detail::call("daybar.coverage", {{"type", Json()}});
    Json cutoff;
    try {
      const Json factors = detail::call("exfactor.coverage", {{"market", wanted}});
      if (factors.is_object()) cutoff = factors.value("cutoff", Json());
    } catch (const std::exception&) {
    }

    Json out = Json::object();
    for (const auto& type : kTypes) {
      if (!coverage.is_object() || !coverage.contains(type) || !coverage[type].is_object() ||
          !coverage[type].contains(wanted) || !coverage[type][wanted].is_object())
        continue;
      for (const auto& [venue, item] : coverage[type][wanted].items()) {
        const Json raw_end = item.is_object() ? item.value("coverage_end", Json()) : Json();
        if (!raw_end.is_string()) continue;
        Json entry = {{"start", item.value("coverage_start", Json())}, {"end", raw_end}, {"raw_end", raw_end}};
        // a stock's adjusted prices end at the exfactor cutoff when it is earlier; an index is not adjusted
        if (type == "stock" && cutoff.is_string()) {
          entry["end"] = std::min(raw_end.get<std::string>(), cutoff.get<std::string>());
          entry["adjust_cutoff"] = cutoff;
        }
        out[type][venue] = entry;
      }
    }
    if (out.empty())
      throw std::runtime_error("get_price_coverage: 服务端没有给出 market='" + market +
                               "' 的覆盖信息。这不表示该市场没有行情，而是拿不到区间——请检查 market 取值。");
    return out;
  });
}

}  // namespace libfinance
