#include <cmath>

#include <arrow/api.h>

#include "internal.hpp"

namespace libfinance::detail {

namespace {

template <typename ArrayType>
Json number(const arrow::Array& array, int64_t row) {
  const auto value = static_cast<const ArrayType&>(array).Value(row);
  if constexpr (std::is_floating_point_v<decltype(value)>) {
    if (std::isnan(value)) return Json();  // pandas' NaN is a missing value
  }
  return value;
}

int64_t days_of(const arrow::TimestampArray& array, int64_t row) {
  const auto unit = static_cast<const arrow::TimestampType&>(*array.type()).unit();
  const int64_t per_day = unit == arrow::TimeUnit::SECOND  ? 86400LL
                          : unit == arrow::TimeUnit::MILLI ? 86400000LL
                          : unit == arrow::TimeUnit::MICRO ? 86400000000LL
                                                           : 86400000000000LL;
  const int64_t value = array.Value(row);
  return value >= 0 ? value / per_day : (value - per_day + 1) / per_day;
}

//: One cell as JSON: numbers and booleans as they are, days as ISO text, other types as text.
Json cell(const arrow::Array& array, int64_t row) {
  if (array.IsNull(row)) return Json();
  switch (array.type_id()) {
    case arrow::Type::BOOL:
      return static_cast<const arrow::BooleanArray&>(array).Value(row);
    case arrow::Type::INT32:
      return number<arrow::Int32Array>(array, row);
    case arrow::Type::INT64:
      return number<arrow::Int64Array>(array, row);
    case arrow::Type::FLOAT:
      return number<arrow::FloatArray>(array, row);
    case arrow::Type::DOUBLE:
      return number<arrow::DoubleArray>(array, row);
    case arrow::Type::STRING:
      return static_cast<const arrow::StringArray&>(array).GetString(row);
    case arrow::Type::LARGE_STRING:
      return static_cast<const arrow::LargeStringArray&>(array).GetString(row);
    case arrow::Type::DATE32:
      return Date::from_days(static_cast<const arrow::Date32Array&>(array).Value(row)).iso();
    case arrow::Type::TIMESTAMP:
      return Date::from_days(static_cast<int32_t>(days_of(static_cast<const arrow::TimestampArray&>(array), row))).iso();
    default: {
      auto scalar = array.GetScalar(row);
      return scalar.ok() ? Json((*scalar)->ToString()) : Json();
    }
  }
}

}  // namespace

std::vector<Json> rows_of(const Table& table) {
  std::vector<Json> rows;
  if (!table) return rows;
  rows.assign(static_cast<size_t>(table->num_rows()), Json::object());
  for (int c = 0; c < table->num_columns(); ++c) {
    const std::string& name = table->field(c)->name();
    size_t row = 0;
    for (const auto& chunk : table->column(c)->chunks())
      for (int64_t i = 0; i < chunk->length(); ++i) rows[row++][name] = cell(*chunk, i);
  }
  return rows;
}

Table column_first(const Table& table, const std::string& name) {
  if (!table) return table;
  const int index = table->schema()->GetFieldIndex(name);
  if (index <= 0) return table;
  auto without = table->RemoveColumn(index);
  if (!without.ok()) throw std::invalid_argument("libfinance: " + without.status().ToString());
  auto moved = (*without)->AddColumn(0, table->field(index), table->column(index));
  if (!moved.ok()) throw std::invalid_argument("libfinance: " + moved.status().ToString());
  return *moved;
}

std::vector<std::string> strings_of(const Table& table, const std::string& name) {
  std::vector<std::string> values;
  if (!table || !table->GetColumnByName(name)) return values;
  for (const auto& chunk : table->GetColumnByName(name)->chunks())
    for (int64_t i = 0; i < chunk->length(); ++i) {
      const Json value = cell(*chunk, i);
      values.push_back(value.is_string() ? value.get<std::string>() : value.is_null() ? "" : value.dump());
    }
  return values;
}

}  // namespace libfinance::detail
