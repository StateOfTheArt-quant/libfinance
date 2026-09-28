// Python: libfinance/api/get_price.py (and warn_if_clamped from libfinance/utils/cache.py).
#include "libfinance/price.hpp"

#include <algorithm>
#include <ctime>
#include <set>

#include <arrow/api.h>
#include <arrow/compute/api.h>

#include "internal.hpp"

namespace libfinance {

namespace {

//: The daily bar fields per kind of security. The stock ones are the upstream daybar's value
//: columns word for word; the server refuses any other name.
const std::vector<std::string> kCommonFields = {"open", "close", "high", "low", "turnover", "volume"};
const std::vector<std::string> kStockFields = {"limit_up", "limit_down"};
const std::vector<std::string> kFundFields = {"limit_up", "limit_down", "num_trades", "iopv"};
const std::vector<std::string> kFundTypes = {"ETF", "LOF", "SF", "FUND"};
const std::string kEarliestStart = "2000-01-04";

bool contains(const std::vector<std::string>& values, const std::string& value) {
  return std::find(values.begin(), values.end(), value) != values.end();
}

void check(const arrow::Status& status) {
  if (!status.ok()) throw std::invalid_argument("libfinance: " + status.ToString());
}

// ---------------------------------------------------------------- arguments

//: "1d" only: the frequency checks of the Python client, in its order and words.
void check_frequency(const std::string& frequency) {
  const char unit = frequency.empty() ? '\0' : frequency.back();
  if (frequency == "tick" || (unit != 'd' && unit != 'w'))
    throw std::invalid_argument("frequency: 目前只支持日频 '1d'，收到 '" + frequency + "'");
  int duration = 0;
  try {
    duration = std::stoi(frequency.substr(0, frequency.size() - 1));
  } catch (const std::exception&) {
    throw std::invalid_argument("invalid literal for int() with base 10: '" +
                                frequency.substr(0, frequency.size() - 1) + "'");
  }
  if (duration < 1 || duration > 240) throw std::invalid_argument("frequency should in range [1, 240]");
  if (unit == 'w' && duration != 1) throw std::invalid_argument("Weekly frequency should be str '1w'");
}

//: `ensure_instruments` as of end_date: the known codes (unknown ones dropped with a warning,
//: duplicates once), and which kinds of security they are.
struct Classified {
  std::vector<std::string> order_book_ids;
  bool stocks = false;
  bool funds = false;
};

Classified classify(const std::vector<std::string>& codes, const DateLike& as_of) {
  const auto type_of = detail::type_by_order_book_id(as_of);
  Classified out;
  for (const auto& code : codes) {
    auto found = type_of.find(code);
    if (found == type_of.end()) {
      detail::warn("invalid order_book_id: " + code);
      continue;
    }
    if (contains(out.order_book_ids, code)) continue;
    out.order_book_ids.push_back(code);
    out.stocks = out.stocks || found->second == "CS";
    out.funds = out.funds || contains(kFundTypes, found->second);
  }
  if (out.order_book_ids.empty())
    throw std::invalid_argument("order_book_ids: at least one valid instrument expected, got none");
  return out;
}

//: `_ensure_fields`: the fields asked for, checked against what these kinds of security have;
//: all of them when none were asked for.
std::vector<std::string> ensure_fields(const Codes& fields, const Classified& kinds) {
  std::vector<std::string> allowed = kCommonFields;
  const std::vector<std::string>* extra[] = {kinds.stocks ? &kStockFields : nullptr, kinds.funds ? &kFundFields : nullptr};
  for (const auto* more : extra)
    if (more != nullptr)
      for (const auto& name : *more)
        if (!contains(allowed, name)) allowed.push_back(name);

  if (!fields.given() || fields.values().empty()) return allowed;
  std::vector<std::string> asked = fields.values();
  std::vector<std::string> repeated;
  for (const auto& name : asked)
    if (std::count(asked.begin(), asked.end(), name) > 1) repeated.push_back(name);
  if (!repeated.empty()) {
    detail::warn("duplicated fields: " + detail::py_list(repeated));
    std::vector<std::string> once;
    for (const auto& name : asked)
      if (!contains(once, name)) once.push_back(name);
    asked = once;
  }
  detail::check_items_in(asked, allowed, "fields");
  return asked;
}

// ---------------------------------------------------------------- warnings before the call

//: today minus years / months / days, the month-end clipped (dateutil's relativedelta).
Date months_back(int years, int months, int days) {
  const std::time_t now = std::time(nullptr);
  std::tm local{};
  localtime_r(&now, &local);
  int month_index = (local.tm_year + 1900) * 12 + local.tm_mon - years * 12 - months;
  const int year = month_index / 12;
  const unsigned month = static_cast<unsigned>(month_index % 12) + 1;
  unsigned day = static_cast<unsigned>(local.tm_mday);
  while (day > 28 && Date::ymd(year, month, day).month() != month) --day;
  return Date::from_days(Date::ymd(year, month, day).days_since_epoch() - days);
}

//: `limits_for`: this caller's limits on a function (describe_capabilities); {} when unknown.
Json limits_for(const std::string& api_name) {
  static detail::VersionedCache<Json> cache;
  try {
    const Json described = cache.get("", [] { return detail::call("describe_capabilities", Json::object()); });
    for (const Json& item : described.value("capabilities", Json::array()))
      if (item.value("api", Json()) == api_name || item.value("name", Json()) == api_name)
        return item.value("limits", Json::object());
  } catch (const std::exception&) {
  }
  return Json::object();
}

//: `warn_if_clamped`: say so when the caller's tier will pull start_date up to its boundary.
void warn_if_clamped(const std::string& api_name, const std::string& start_date) {
  const Json window = limits_for(api_name).value("clamp_date_window", Json());
  if (!window.is_object()) return;
  const std::string boundary =
      months_back(window.value("years", 0), window.value("months", 0), window.value("days", 0)).iso();
  if (start_date >= boundary) return;
  detail::warn(api_name + ": 可查区间的起点是 " + boundary + "，比它更早的 start_date=" + start_date +
               " 会被服务端夹到边界（end_date 早于边界时也会一起上拉，结果可能是空表）。");
}

//: `_warn_beyond_coverage`: an end_date past the bars is refused by the server; say why first.
void warn_beyond_coverage(const std::string& end_date) {
  std::string latest;
  try {
    for (const auto& [mic, entry] : get_price_coverage().items()) {
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

//: `_to_panel`: order_book_id (trading_code + "." + symbol_namespace) and datetime (session_date)
//: first, sorted by both. A shape it does not know is returned as it came.
Table to_panel(const Table& bars) {
  if (!bars || bars->num_rows() == 0 || !bars->GetColumnByName("session_date")) return bars;
  const char* namespace_column = bars->GetColumnByName("symbol_namespace") ? "symbol_namespace"
                                 : bars->GetColumnByName("exchange_id")    ? "exchange_id"
                                                                           : nullptr;
  Table table = bars;
  if (namespace_column != nullptr && bars->GetColumnByName("trading_code")) {
    const auto codes = detail::strings_of(bars, "trading_code");
    const auto namespaces = detail::strings_of(bars, namespace_column);
    arrow::StringBuilder ids;
    for (size_t i = 0; i < codes.size(); ++i) check(ids.Append(codes[i] + "." + namespaces[i]));
    std::shared_ptr<arrow::Array> id_array;
    check(ids.Finish(&id_array));
    for (const char* dropped : {namespace_column, "trading_code"}) {
      auto without = table->RemoveColumn(table->schema()->GetFieldIndex(dropped));
      check(without.status());
      table = *without;
    }
    auto added = table->AddColumn(0, arrow::field("order_book_id", arrow::utf8()),
                                  std::make_shared<arrow::ChunkedArray>(id_array));
    check(added.status());
    table = *added;
  } else if (!bars->GetColumnByName("order_book_id")) {
    return bars;
  }
  table = detail::column_first(table, "order_book_id");

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
  check_frequency(frequency);
  detail::check_items_in({adjust_type}, {"pre", "post", "none"}, "adjust_type");

  // codes are resolved as of the window's end, not today: a security delisted since is still known
  const Classified kinds = classify(detail::list_of(order_book_ids, "order_book_ids"), end_date);

  std::string start = start_date.iso();
  const std::string end = end_date.iso();
  if (start < kEarliestStart) {
    detail::warn("start_date is earlier than 2000-01-04, adjusted to 2000-01-04");
    start = kEarliestStart;
  }
  warn_if_clamped("get_price", start);
  warn_beyond_coverage(end);

  const Table bars = detail::call_table("get_price", {{"order_book_ids", kinds.order_book_ids},
                                                     {"start_date", start},
                                                     {"end_date", end},
                                                     {"frequency", frequency},
                                                     {"fields", ensure_fields(fields, kinds)},
                                                     {"skip_suspended", skip_suspended},
                                                     {"include_now", include_now},
                                                     {"adjust_type", adjust_type},
                                                     {"adjust_orig", detail::iso_or_null(adjust_orig)}});
  return to_panel(bars);
}

Json get_price_coverage(const std::string& market) {
  static detail::VersionedCache<Json> cache;
  return cache.get(market, [&] {
    const Json args = {{"market", market}};
    Json info = detail::call("daybar.dataset_info", args);
    if (!info.is_object()) info = Json::object();
    // CN comes by MIC ({"XSHG": {...}, "XSHE": {...}}); US is one dataset's flat dict with its mic
    if (info.contains("mic") && info.contains("dataset")) {
      std::string mic = market;
      std::transform(mic.begin(), mic.end(), mic.begin(), [](unsigned char c) { return std::toupper(c); });
      if (info["mic"].is_string() && !info["mic"].get<std::string>().empty()) mic = info["mic"].get<std::string>();
      info = Json{{mic, info}};
    }
    Json cutoff;
    try {
      const Json factors = detail::call("exfactor.dataset_info", args);
      if (factors.is_object()) cutoff = factors.value("cutoff", Json());
    } catch (const std::exception&) {
    }

    Json out = Json::object();
    for (const auto& [mic, item] : info.items()) {
      if (!item.is_object()) continue;
      const Json raw_end = item.value("coverage_end", Json());
      // the adjusted prices end at the exfactor cutoff when it is earlier; US has no day-level end
      Json end = raw_end;
      if (cutoff.is_string() && (end.is_null() || end.get<std::string>() > cutoff.get<std::string>())) end = cutoff;
      if (end.is_null()) continue;
      Json entry = {{"start", item.value("coverage_start", Json())}, {"end", end}, {"raw_end", raw_end}};
      if (cutoff.is_string()) entry["adjust_cutoff"] = cutoff;
      out[mic] = entry;
    }
    if (out.empty())
      throw std::runtime_error("get_price_coverage: 服务端没有给出 market='" + market +
                               "' 的覆盖信息。这不表示该市场没有行情，而是拿不到区间——请检查 market 取值。");
    return out;
  });
}

}  // namespace libfinance
