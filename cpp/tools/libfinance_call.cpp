// libfinance-call: one libfinance function by name, keyword arguments as JSON, the answer as JSON.
//
//   libfinance-call get_price '{"order_book_ids": ["600000.XSHG"], "start_date": "2025-06-02", "end_date": "2025-06-06"}'
//   libfinance-call --list
//
// Each name goes to the typed C++ function of the same name (so the table below is also the list of
// what the C++ client implements -- conformance/ checks it against contract/contract.json). Tables
// print as {"columns": [...], "rows": [[...], ...]}, dates as ISO days. A failure prints
// "<Kind>: <message>" on stderr and exits 1: the server's error kind, or ValueError /
// CalendarCoverageError / RuntimeError for what the client itself refused.
#include <functional>
#include <iostream>
#include <map>
#include <string>

#include <libfinance/libfinance.hpp>

#include "internal.hpp"

namespace lf = libfinance;
using lf::Json;

namespace {

// ---------------------------------------------------------------- arguments from JSON

bool has(const Json& args, const char* name) { return args.contains(name) && !args[name].is_null(); }

lf::Codes codes(const Json& args, const char* name) {
  if (!has(args, name)) return {};
  const Json& value = args[name];
  if (value.is_string()) return lf::Codes(value.get<std::string>());
  return lf::Codes(value.get<std::vector<std::string>>());
}

lf::DateLike date(const Json& args, const char* name) {
  if (!has(args, name)) throw std::invalid_argument(std::string("missing required argument: '") + name + "'");
  const Json& value = args[name];
  return value.is_number_integer() ? lf::DateLike(value.get<int>()) : lf::DateLike(value.get<std::string>());
}

std::optional<lf::DateLike> optional_date(const Json& args, const char* name) {
  if (!has(args, name)) return std::nullopt;
  return date(args, name);
}

std::string text(const Json& args, const char* name, const std::string& fallback) {
  return has(args, name) ? args[name].get<std::string>() : fallback;
}

std::string required_text(const Json& args, const char* name) {
  if (!has(args, name)) throw std::invalid_argument(std::string("missing required argument: '") + name + "'");
  return args[name].get<std::string>();
}

std::optional<std::string> optional_text(const Json& args, const char* name) {
  if (!has(args, name)) return std::nullopt;
  return args[name].get<std::string>();
}

int integer(const Json& args, const char* name, int fallback) { return has(args, name) ? args[name].get<int>() : fallback; }

std::optional<int> optional_integer(const Json& args, const char* name) {
  return has(args, name) ? std::optional<int>(args[name].get<int>()) : std::nullopt;
}

bool flag(const Json& args, const char* name, bool fallback) { return has(args, name) ? args[name].get<bool>() : fallback; }

std::vector<std::string> strings(const Json& args, const char* name) {
  return has(args, name) ? args[name].get<std::vector<std::string>>() : std::vector<std::string>{};
}

// ---------------------------------------------------------------- answers as JSON

Json table(const lf::Table& value) {
  if (!value) return Json();
  Json columns = Json::array();
  for (const auto& field : value->schema()->fields()) columns.push_back(field->name());
  Json rows = Json::array();
  for (const Json& row : lf::detail::rows_of(value)) {
    Json cells = Json::array();
    for (const auto& name : columns) cells.push_back(row[name.get<std::string>()]);
    rows.push_back(cells);
  }
  return {{"columns", columns}, {"rows", rows}};
}

Json days(const std::vector<lf::Date>& values) {
  Json out = Json::array();
  for (auto value : values) out.push_back(value.iso());
  return out;
}

using Function = std::function<Json(const Json&)>;

const std::map<std::string, Function>& functions() {
  static const std::map<std::string, Function> table_of_functions = {
      // calendar
      {"get_all_trading_dates", [](const Json& a) { return days(lf::get_all_trading_dates(text(a, "market", "cn"))); }},
      {"get_calendar_coverage",
       [](const Json& a) {
         const auto coverage = lf::get_calendar_coverage(text(a, "market", "cn"));
         return Json{{"history_start", coverage.history_start.iso()},
                     {"confirmed_through", coverage.confirmed_through.iso()}};
       }},
      {"get_trading_dates",
       [](const Json& a) {
         return days(lf::get_trading_dates(date(a, "start_date"), date(a, "end_date"), text(a, "market", "cn")));
       }},
      {"get_previous_trading_date",
       [](const Json& a) {
         return Json(lf::get_previous_trading_date(date(a, "date"), integer(a, "n", 1), text(a, "market", "cn")).iso());
       }},
      {"get_next_trading_date",
       [](const Json& a) {
         return Json(lf::get_next_trading_date(date(a, "date"), integer(a, "n", 1), text(a, "market", "cn")).iso());
       }},
      {"is_trading_date", [](const Json& a) { return Json(lf::is_trading_date(date(a, "date"), text(a, "market", "cn"))); }},
      {"get_n_trading_dates_until",
       [](const Json& a) {
         if (!has(a, "n")) throw std::invalid_argument("missing required argument: 'n'");
         return days(lf::get_n_trading_dates_until(date(a, "date"), a["n"].get<int>(), text(a, "market", "cn")));
       }},
      {"count_trading_dates",
       [](const Json& a) {
         return Json(lf::count_trading_dates(date(a, "start_date"), date(a, "end_date"), text(a, "market", "cn")));
       }},
      // instrument
      {"all_instruments",
       [](const Json& a) {
         return table(lf::all_instruments(codes(a, "type"), optional_text(a, "market"), codes(a, "source"),
                                          optional_date(a, "as_of"), flag(a, "cached", true)));
       }},
      {"instruments",
       [](const Json& a) {
         Json out = Json::array();
         for (const auto& found : lf::instruments(codes(a, "order_book_ids"), optional_date(a, "as_of"),
                                                     flag(a, "last_known", false)))
           out.push_back(found.fields());
         return out;
       }},
      // price
      {"get_price",
       [](const Json& a) {
         return table(lf::get_price(codes(a, "order_book_ids"), date(a, "start_date"), date(a, "end_date"),
                                    text(a, "frequency", "1d"), codes(a, "fields"), flag(a, "skip_suspended", false),
                                    flag(a, "include_now", true), text(a, "adjust_type", "pre"),
                                    optional_date(a, "adjust_orig")));
       }},
      {"get_price_coverage", [](const Json& a) { return lf::get_price_coverage(text(a, "market", "cn")); }},
      // corporate actions
      {"get_dividends",
       [](const Json& a) {
         return table(lf::get_dividends(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                        optional_date(a, "end_date"), codes(a, "fields"), optional_date(a, "as_of")));
       }},
      {"get_splits",
       [](const Json& a) {
         return table(lf::get_splits(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                     optional_date(a, "end_date"), codes(a, "fields"), optional_date(a, "as_of")));
       }},
      {"get_allotments",
       [](const Json& a) {
         return table(lf::get_allotments(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                         optional_date(a, "end_date"), codes(a, "fields"), optional_date(a, "as_of")));
       }},
      {"get_spinoffs",
       [](const Json& a) {
         return table(lf::get_spinoffs(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                       optional_date(a, "end_date"), codes(a, "fields"), optional_date(a, "as_of")));
       }},
      // exfactor
      {"get_ex_factor",
       [](const Json& a) {
         return table(lf::get_ex_factor(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                        optional_date(a, "end_date")));
       }},
      // financials
      {"get_pit_financials_ex",
       [](const Json& a) {
         return table(lf::get_pit_financials_ex(codes(a, "order_book_ids"), codes(a, "fields"),
                                                required_text(a, "start_quarter"), required_text(a, "end_quarter"),
                                                optional_date(a, "as_of"), text(a, "statements", "latest")));
       }},
      {"get_factor",
       [](const Json& a) {
         return table(lf::get_factor(codes(a, "order_book_ids"), codes(a, "factors"), required_text(a, "start_quarter"),
                                     required_text(a, "end_quarter"), optional_date(a, "as_of")));
       }},
      // index, industry, theme: members and weights
      {"get_index_constituents",
       [](const Json& a) { return lf::get_index_constituents(required_text(a, "order_book_id"), optional_date(a, "as_of")); }},
      {"get_instrument_indices",
       [](const Json& a) {
         return table(lf::get_instrument_indices(codes(a, "order_book_ids"), optional_text(a, "source"),
                                                 optional_date(a, "as_of")));
       }},
      {"get_index_weights",
       [](const Json& a) { return table(lf::get_index_weights(required_text(a, "order_book_id"), optional_date(a, "as_of"))); }},
      {"get_industry_constituents",
       [](const Json& a) { return lf::get_industry_constituents(required_text(a, "order_book_id"), optional_date(a, "as_of")); }},
      {"get_instrument_industry",
       [](const Json& a) {
         return table(lf::get_instrument_industry(codes(a, "order_book_ids"), optional_text(a, "source"),
                                                  optional_integer(a, "level"), optional_date(a, "as_of")));
       }},
      {"get_industry_weights",
       [](const Json& a) {
         return table(lf::get_industry_weights(required_text(a, "order_book_id"), optional_date(a, "as_of")));
       }},
      {"get_theme_constituents",
       [](const Json& a) { return lf::get_theme_constituents(required_text(a, "order_book_id"), optional_date(a, "as_of")); }},
      {"get_instrument_themes",
       [](const Json& a) {
         return table(lf::get_instrument_themes(codes(a, "order_book_ids"), optional_text(a, "source"),
                                                optional_date(a, "as_of")));
       }},
      {"get_theme_weights",
       [](const Json& a) { return table(lf::get_theme_weights(required_text(a, "order_book_id"), optional_date(a, "as_of"))); }},
      // shares, quotes
      {"get_shares",
       [](const Json& a) {
         return table(lf::get_shares(codes(a, "order_book_ids"), optional_date(a, "start_date"),
                                     optional_date(a, "end_date"), codes(a, "fields"),
                                     optional_date(a, "as_of")));
       }},
      {"get_last_quotes", [](const Json& a) { return lf::get_last_quotes(strings(a, "order_book_ids")); }},
  };
  return table_of_functions;
}

int fail(const std::string& kind, const std::string& message) {
  std::cerr << kind << ": " << message << "\n";
  return 1;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--list") {
    for (const auto& [name, function] : functions()) std::cout << name << "\n";
    return 0;
  }
  if (argc < 2 || argc > 3) {
    std::cerr << "usage: " << argv[0] << " <function> ['<JSON keyword arguments>']  |  " << argv[0] << " --list\n";
    return 2;
  }
  auto found = functions().find(argv[1]);
  if (found == functions().end()) return fail("UnknownFunction", argv[1]);
  lf::set_warning_handler([](const std::string& message) { std::cerr << "warning: " << message << "\n"; });
  try {
    const Json args = argc == 3 ? Json::parse(argv[2]) : Json::object();
    std::cout << found->second(args).dump() << "\n";
  } catch (const lf::RpcError& error) {
    return fail(error.kind().empty() ? "RpcError" : error.kind(), error.message());
  } catch (const lf::CalendarCoverageError& error) {
    return fail("CalendarCoverageError", error.what());
  } catch (const std::invalid_argument& error) {
    return fail("ValueError", error.what());
  } catch (const std::exception& error) {
    return fail("RuntimeError", error.what());
  }
  return 0;
}
