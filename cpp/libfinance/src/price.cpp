// Python: libfinance/api/get_price.py (and warn_if_clamped from libfinance/utils/cache.py).
#include "libfinance/price.hpp"

#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <exception>
#include <future>

#include <arrow/api.h>
#include <arrow/compute/api.h>
#include <arrow/util/config.h>
#if ARROW_VERSION_MAJOR >= 21
#include <arrow/compute/initialize.h>
#endif

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
  // 空列表不是"全部字段"（那是不给），而是一张没有列的表——几乎一定是调用方的错
  if (asked.empty()) throw std::invalid_argument("fields: at least one field expected (omit it for all fields)");
  for (const auto& name : asked) {
    if (!contains(once, name)) once.push_back(name);
    else if (!contains(repeated, name)) repeated.push_back(name);
  }
  if (!repeated.empty()) detail::warn("duplicated fields: " + detail::py_list(repeated));
  return once;
}

// ---------------------------------------------------------------- warnings before the call

//: `_warn_beyond_coverage`: an end_date past the bars is refused by the server; say why first.
//: 所查代码所在的市场（Python 的 _markets_of）：交易所后缀 XSHG/XSHE/XBSE 是 cn，其余是 us。
std::vector<std::string> markets_of(const std::vector<std::string>& ids) {
  bool cn = false, us = false;
  for (const auto& id : ids) {
    const std::string venue = id.substr(id.rfind('.') + 1);
    (venue == "XSHG" || venue == "XSHE" || venue == "XBSE" ? cn : us) = true;
  }
  std::vector<std::string> out;
  if (cn) out.emplace_back("cn");
  if (us) out.emplace_back("us");
  return out;
}

void warn_beyond_coverage(const std::string& end_date, const std::vector<std::string>& ids) {
  std::string latest;
  try {
    for (const auto& market : markets_of(ids))
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
#if ARROW_VERSION_MAJOR >= 21
  // Arrow 21+: the compute kernels live in libarrow_compute and are registered on first use;
  // without this Cast / SortIndices fail with "No function registered with name".
  static const arrow::Status compute = arrow::compute::Initialize();
  check(compute);
#endif
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

//: 结果为空，或第一行晚于 start_date（可能被分档限制夹紧）。
bool starts_after(const Table& panel, const std::string& start) {
  if (!panel) return false;
  if (panel->num_rows() == 0) return true;
  const auto column = panel->GetColumnByName("datetime");
  if (!column) return false;
  const int64_t start_ms = static_cast<int64_t>(DateLike(start).date().days_since_epoch()) * 86400000LL;
  for (const auto& chunk : column->chunks()) {
    const auto& values = static_cast<const arrow::TimestampArray&>(*chunk);
    for (int64_t i = 0; i < values.length(); ++i)
      if (values.IsValid(i) && values.Value(i) <= start_ms) return false;
  }
  return true;
}

//: `_warn_unknown_codes`: when a code has no row at all, tell "misspelt / not listed that day" from "no bars
//: in this window". instruments is asked only then, so a normal call pays no extra round trip.
void warn_unknown_codes(const Table& panel, const std::vector<std::string>& ids, const std::string& end) {
  if (!panel) return;
  const auto column = panel->GetColumnByName("order_book_id");
  if (!column) return;
  std::vector<std::string> present;
  for (const auto& chunk : column->chunks()) {
    if (chunk->type_id() != arrow::Type::STRING) return;
    const auto& values = static_cast<const arrow::StringArray&>(*chunk);
    for (int64_t i = 0; i < values.length(); ++i) {
      if (!values.IsValid(i)) continue;
      const std::string code = values.GetString(i);
      if (present.empty() || present.back() != code)  // sorted by order_book_id
        if (!contains(present, code)) present.push_back(code);
    }
  }
  std::vector<std::string> missing;
  for (const auto& code : ids)
    if (!contains(present, code)) missing.push_back(code);
  if (missing.empty()) return;
  std::vector<std::string> unknown;
  try {
    const Json found =
        detail::call("instruments", {{"order_book_ids", missing}, {"as_of", end}, {"last_known", true}});
    for (const auto& code : missing) {
      bool known = false;
      if (found.is_array())
        for (const Json& item : found)
          if (item.is_object() && item.value("order_book_id", Json()) == code) known = true;
      if (!known) unknown.push_back(code);
    }
  } catch (const std::exception&) {
    return;
  }
  if (!unknown.empty())
    detail::warn("get_price: " + detail::py_list(unknown) + " 在 " + end +
                 " 不是已知的证券代码，结果中没有它们的行（不是停牌或缺数据）。用 instruments() 核对代码。");
}

// ---------------------------------------------------------------- a large query, split (PERF-03)

//: 一个连接上一份答复的目标行数，与 Python 的 _ROWS_PER_PART 相同。跨境链路上每个 TCP 连接前 1–2 MB 很快、
//: 之后降到 50–80 KB/s（2026-11-17 实测）；日线压缩后约 45 B/行，1 万行约 0.45 MB，落在快的那一段里。
constexpr int64_t kRowsPerPart = 10000;

//: 一次查询最多切成几份：LIBFINANCE_PARALLEL（默认 8，与 Python 的 client.PARALLEL_CONNECTIONS 相同）。
//: 各份经 RpcClient 的连接池并行，池小于份数时多出的排队等连接。
int64_t parallel_parts() {
  const char* text = std::getenv("LIBFINANCE_PARALLEL");
  if (text == nullptr || *text == '\0') return 8;
  char* end = nullptr;
  errno = 0;
  const long value = std::strtol(text, &end, 10);
  if (errno != 0 || end == text || *end != '\0') return 8;
  return std::clamp<long>(value, 1, 1024);
}

//: 区间内的工作日数（pandas 的 bdate_range），至少 1。
int64_t weekdays(const std::string& start, const std::string& end) {
  const int32_t first = DateLike(start).date().days_since_epoch(), last = DateLike(end).date().days_since_epoch();
  int64_t count = 0;
  for (int32_t day = first; day <= last; ++day)
    if (((day % 7 + 7) % 7 + 3) % 7 < 5) ++count;  // 1970-01-01 is a Thursday; Monday is 0
  return std::max<int64_t>(1, count);
}

//: `_parts`：按估计行数（代码数 × 工作日）把代码切成几份；小查询不切。
std::vector<std::vector<std::string>> split_codes(const std::vector<std::string>& ids, const std::string& start,
                                                  const std::string& end) {
  const int64_t n = static_cast<int64_t>(ids.size());
  if (n <= 1) return {ids};
  const int64_t wanted = (n * weekdays(start, end) + kRowsPerPart - 1) / kRowsPerPart;
  const int64_t count = std::max<int64_t>(1, std::min({parallel_parts(), wanted, n}));
  const int64_t size = (n + count - 1) / count;
  std::vector<std::vector<std::string>> parts;
  for (int64_t first = 0; first < n; first += size)
    parts.emplace_back(ids.begin() + first, ids.begin() + std::min(n, first + size));
  return parts;
}

//: `_fetch`：每份一个请求、并行，等全部结束；有拒绝时抛出按顺序的第一个。合并后经 to_panel 排序，
//: 与一次查询相同；某份不是表或各份的列对不上时，按一次查询的结果给。
Table fetch_bars(const std::vector<std::string>& ids, const Json& args, const std::string& start,
                 const std::string& end) {
  const auto query = [&args](const std::vector<std::string>& codes) {
    Json part = args;
    part["order_book_ids"] = codes;
    return detail::call_table("get_price", part);
  };
  const auto parts = split_codes(ids, start, end);
  if (parts.size() == 1) return query(ids);
  std::vector<std::future<Table>> pending;
  for (const auto& codes : parts) pending.push_back(std::async(std::launch::async, query, std::cref(codes)));
  std::vector<Table> tables;
  std::exception_ptr first_error;
  for (auto& part : pending) {
    try {
      tables.push_back(part.get());
    } catch (...) {
      if (!first_error) first_error = std::current_exception();
    }
  }
  if (first_error) std::rethrow_exception(first_error);
  for (const auto& table : tables)
    if (!table) return query(ids);
  arrow::ConcatenateTablesOptions options;
  options.unify_schemas = true;
  auto merged = arrow::ConcatenateTables(tables, options);
  if (!merged.ok()) return query(ids);
  return *merged;
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
  // 分档夹紧、超出覆盖两项提示都要先取元数据（冷启动 4 个串行往返），而它们只在结果不完整时才有意义：
  // 放到查询之后，只在需要时做。成功且从 start_date 起就有数据的调用只付 1 个往返。
  // daybar routes the codes (stocks and indexes alike) by instrument as of end_date
  Table bars;
  try {
    bars = fetch_bars(ids,
                      {{"order_book_ids", ids},
                       {"start_date", start},
                       {"end_date", end},
                       {"frequency", frequency},
                       {"fields", fields_argument(fields)},
                       {"skip_suspended", skip_suspended},
                       {"include_now", include_now},
                       {"adjust_type", adjust_type},
                       {"adjust_orig", detail::iso_or_null(adjust_orig)}},
                      start, end);
  } catch (const RpcError& error) {
    if (error.kind() == "CoverageError" || error.message().find("outside coverage") != std::string::npos)
      warn_beyond_coverage(end, ids);   // 说出覆盖上界，再把服务端的拒绝原样抛出
    throw;
  }
  Table panel = to_panel(bars);
  if (starts_after(panel, start)) detail::warn_if_clamped("get_price", start);
  warn_unknown_codes(panel, ids, end);
  return panel;
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
