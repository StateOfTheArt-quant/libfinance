// Python: libfinance/api/corporate_actions.py. The four functions share one set of arguments.
#include "libfinance/corporate_actions.hpp"

#include <stdexcept>

#include <arrow/api.h>

#include "internal.hpp"

namespace libfinance {

namespace {

//: `_args`: codes (at least one), dates as ISO days in order, fields as a list.
Json arguments(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
               const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Json ids = detail::order_book_ids(order_book_ids);
  const Json start = detail::iso_or_null(start_date), end = detail::iso_or_null(end_date);
  detail::check_date_range(start, end);
  return {{"order_book_ids", ids},
          {"start_date", start},
          {"end_date", end},
          {"fields", detail::list_or_null(fields, "fields")},
          {"as_of", detail::iso_or_null(as_of)}};
}

void check(const arrow::Status& status) {
  if (!status.ok()) throw std::runtime_error("libfinance: " + status.ToString());
}

template <typename DecimalArray, typename Decimal>
std::shared_ptr<arrow::Array> to_float64(const arrow::Array& chunk, int32_t scale) {
  const auto& decimals = static_cast<const DecimalArray&>(chunk);
  arrow::DoubleBuilder builder;
  check(builder.Reserve(decimals.length()));
  for (int64_t i = 0; i < decimals.length(); ++i) {
    if (decimals.IsNull(i)) {
      builder.UnsafeAppendNull();
    } else {
      builder.UnsafeAppend(Decimal(decimals.GetValue(i)).ToDouble(scale));
    }
  }
  std::shared_ptr<arrow::Array> out;
  check(builder.Finish(&out));
  return out;
}

}  // namespace

namespace detail {

Table decimals_to_float64(const Table& table) {
  if (!table) return table;
  std::vector<std::shared_ptr<arrow::Field>> fields;
  std::vector<std::shared_ptr<arrow::ChunkedArray>> columns;
  bool changed = false;
  for (int i = 0; i < table->num_columns(); ++i) {
    const auto& field = table->schema()->field(i);
    const auto& column = table->column(i);
    const auto id = field->type()->id();
    if (id != arrow::Type::DECIMAL128 && id != arrow::Type::DECIMAL256) {
      fields.push_back(field);
      columns.push_back(column);
      continue;
    }
    const int32_t scale = static_cast<const arrow::DecimalType&>(*field->type()).scale();
    arrow::ArrayVector chunks;
    for (const auto& chunk : column->chunks())
      chunks.push_back(id == arrow::Type::DECIMAL128 ? to_float64<arrow::Decimal128Array, arrow::Decimal128>(*chunk, scale)
                                                     : to_float64<arrow::Decimal256Array, arrow::Decimal256>(*chunk, scale));
    fields.push_back(arrow::field(field->name(), arrow::float64(), field->nullable(), field->metadata()));
    columns.push_back(std::make_shared<arrow::ChunkedArray>(chunks, arrow::float64()));
    changed = true;
  }
  if (!changed) return table;
  return arrow::Table::Make(arrow::schema(fields, table->schema()->metadata()), columns, table->num_rows());
}

}  // namespace detail

Table get_dividends(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                    const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Table table = detail::call_table("get_dividends", arguments(order_book_ids, start_date, end_date, fields, as_of));
  return detail::decimals_to_float64(table);
}

Table get_splits(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                 const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Table table = detail::call_table("get_splits", arguments(order_book_ids, start_date, end_date, fields, as_of));
  return detail::decimals_to_float64(table);
}

Table get_allotments(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                     const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Table table = detail::call_table("get_allotments", arguments(order_book_ids, start_date, end_date, fields, as_of));
  return detail::decimals_to_float64(table);
}

Table get_spinoffs(const Codes& order_book_ids, const std::optional<DateLike>& start_date,
                   const std::optional<DateLike>& end_date, const Codes& fields, const std::optional<DateLike>& as_of) {
  const Table table = detail::call_table("get_spinoffs", arguments(order_book_ids, start_date, end_date, fields, as_of));
  return detail::decimals_to_float64(table);
}

}  // namespace libfinance
