// Python: libfinance/api/factors.py.
#include "libfinance/factors.hpp"

#include <arrow/api.h>

#include "internal.hpp"

namespace libfinance {

Table get_factor_exposure(const Codes& order_book_ids, const Codes& factor_names, const DateLike& start_date,
                          const DateLike& end_date, const Codes& universe) {
  const std::vector<std::string> ids = detail::order_book_ids(order_book_ids);
  const std::vector<std::string> names = detail::list_of(factor_names, "factor_names");
  if (names.empty()) throw std::invalid_argument("factor_names: at least one factor name expected");
  if (end_date.date() < start_date.date())
    throw std::invalid_argument("start_date " + start_date.iso() + " is after end_date " + end_date.iso());
  detail::warn_if_clamped("get_factor_exposure", start_date.iso());
  detail::warn_if_truncated("get_factor_exposure", ids.size());
  return detail::call_table("get_factor_exposure", {{"order_book_ids", ids},
                                                    {"factor_names", names},
                                                    {"start_date", start_date.iso()},
                                                    {"end_date", end_date.iso()},
                                                    {"universe", detail::list_or_null(universe, "universe")}});
}

Table list_factor_libraries() {
  const Json rows = detail::call("list_factor_libraries", Json::object());
  arrow::StringBuilder name, version, description;
  arrow::Int64Builder factors;
  const auto text = [](const Json& row, const char* key) {
    const Json value = row.value(key, Json());
    return value.is_string() ? value.get<std::string>() : std::string();
  };
  for (const Json& row : rows) {
    (void)name.Append(text(row, "name"));
    (void)version.Append(text(row, "version"));
    (void)factors.Append(row.value("factors", Json(0)).get<int64_t>());
    (void)description.Append(text(row, "description"));
  }
  std::vector<std::shared_ptr<arrow::Array>> columns(4);
  for (auto [builder, i] : std::vector<std::pair<arrow::ArrayBuilder*, int>>{{&name, 0}, {&version, 1}, {&factors, 2},
                                                                            {&description, 3}})
    if (!builder->Finish(&columns[i]).ok()) throw std::runtime_error("list_factor_libraries: cannot build the table");
  return arrow::Table::Make(arrow::schema({arrow::field("name", arrow::utf8()), arrow::field("version", arrow::utf8()),
                                           arrow::field("factors", arrow::int64()),
                                           arrow::field("description", arrow::utf8())}),
                            columns);
}

std::vector<std::string> list_factors(const std::optional<std::string>& library) {
  return detail::call("list_factors", {{"library", detail::text_or_null(library)}}).get<std::vector<std::string>>();
}

}  // namespace libfinance
