// What the examples print, and how they run: the C++ counterpart of the Python examples' print().
#pragma once

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <utility>
#include <string>
#include <vector>

#include <arrow/api.h>

#include <libfinance/libfinance.hpp>

namespace lf = libfinance;

namespace detail {

//: Columns a UTF-8 string takes on a terminal: CJK and full-width characters take two.
inline size_t display_width(const std::string& text) {
  size_t width = 0;
  for (size_t i = 0; i < text.size();) {
    const auto byte = static_cast<unsigned char>(text[i]);
    uint32_t code = byte;
    size_t length = 1;
    if (byte >= 0xF0) code = byte & 0x07, length = 4;
    else if (byte >= 0xE0) code = byte & 0x0F, length = 3;
    else if (byte >= 0xC0) code = byte & 0x1F, length = 2;
    for (size_t k = 1; k < length && i + k < text.size(); ++k)
      code = (code << 6) | (static_cast<unsigned char>(text[i + k]) & 0x3F);
    const bool wide = (code >= 0x1100 && code <= 0x115F) || (code >= 0x2E80 && code <= 0xA4CF) ||
                      (code >= 0xAC00 && code <= 0xD7A3) || (code >= 0xF900 && code <= 0xFAFF) ||
                      (code >= 0xFE30 && code <= 0xFE4F) || (code >= 0xFF00 && code <= 0xFF60) ||
                      (code >= 0xFFE0 && code <= 0xFFE6);
    width += wide ? 2 : 1;
    i += length;
  }
  return width;
}

inline bool is_float(const arrow::Array& column) {
  return column.type_id() == arrow::Type::DOUBLE || column.type_id() == arrow::Type::FLOAT;
}

inline double float_at(const std::shared_ptr<arrow::Array>& column, int64_t row) {
  return column->type_id() == arrow::Type::DOUBLE ? std::static_pointer_cast<arrow::DoubleArray>(column)->Value(row)
                                                  : std::static_pointer_cast<arrow::FloatArray>(column)->Value(row);
}

//: Decimals a float column is printed with, as pandas picks them: the fewest (at most 6) that show
//: every value of the rows shown.
inline int decimals(const std::shared_ptr<arrow::Array>& column, int64_t rows) {
  int most = 0;
  for (int64_t r = 0; r < rows; ++r) {
    if (column->IsNull(r)) continue;
    std::ostringstream out;
    out << std::fixed << std::setprecision(6) << float_at(column, r);
    std::string text = out.str();
    text.erase(text.find_last_not_of('0') + 1);
    const auto point = text.find('.');
    most = std::max(most, static_cast<int>(text.size() - point - 1));
  }
  return most;
}

//: One cell as pandas prints it: floats with their column's decimals, a midnight timestamp as its
//: date, a list as [a, b], null as NaN.
inline std::string cell(const std::shared_ptr<arrow::Array>& column, int64_t row, int places) {
  if (column->IsNull(row)) return "NaN";
  if (is_float(*column)) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(places) << float_at(column, row);
    return out.str();
  }
  if (column->type_id() == arrow::Type::LIST) {
    const auto list = std::static_pointer_cast<arrow::ListArray>(column);
    const auto items = list->value_slice(row);
    std::string text = "[";
    for (int64_t i = 0; i < items->length(); ++i)
      text += (i ? ", " : "") + (items->IsNull(i) ? std::string("None") : items->GetScalar(i).ValueOrDie()->ToString());
    return text + "]";
  }
  std::string text = column->GetScalar(row).ValueOrDie()->ToString();
  if (column->type_id() == arrow::Type::TIMESTAMP) {
    const auto midnight = text.find(" 00:00:00");
    if (midnight != std::string::npos && text.find_first_not_of("0.:", midnight + 1) == std::string::npos)
      text.resize(midnight);
  }
  return text;
}

}  // namespace detail

//: A table as rows: a header line, its first `rows` rows (all of them when 0), then its shape.
inline void show(const lf::Table& table, int64_t rows = 5) {
  if (!table) {
    std::cout << "None\n";
    return;
  }
  const auto batch = table->CombineChunksToBatch().ValueOrDie();
  const int columns = batch->num_columns();
  const int64_t shown = rows > 0 ? std::min<int64_t>(rows, batch->num_rows()) : batch->num_rows();
  std::vector<std::vector<std::string>> text(columns);
  std::vector<size_t> width(columns);
  for (int c = 0; c < columns; ++c) {
    text[c].push_back(batch->schema()->field(c)->name());
    const int places = detail::is_float(*batch->column(c)) ? detail::decimals(batch->column(c), shown) : 0;
    for (int64_t r = 0; r < shown; ++r) text[c].push_back(detail::cell(batch->column(c), r, places));
    for (const auto& value : text[c]) width[c] = std::max(width[c], detail::display_width(value));
  }
  for (int64_t r = 0; r <= shown; ++r) {
    for (int c = 0; c < columns; ++c) {
      const std::string& value = text[c][static_cast<size_t>(r)];
      std::cout << value;
      if (c + 1 < columns) std::cout << std::string(width[c] - detail::display_width(value) + 2, ' ');
    }
    std::cout << "\n";
  }
  if (shown < batch->num_rows()) std::cout << "...\n";
  std::cout << "[" << batch->num_rows() << " rows x " << columns << " columns]\n";
}

inline void show(const lf::Json& value) { std::cout << value.dump(2) << "\n"; }

inline void show(const std::vector<lf::Date>& dates) {
  std::cout << "[";
  for (size_t i = 0; i < dates.size(); ++i) std::cout << (i ? ", " : "") << dates[i];
  std::cout << "] (" << dates.size() << " days)\n";
}

inline void show(lf::Date date) { std::cout << date << "\n"; }
inline void show(bool value) { std::cout << (value ? "True" : "False") << "\n"; }
inline void show(int value) { std::cout << value << "\n"; }

//: A list's length and its first `n` items: Python's print(len(items), items[:n]).
inline void show_list(const lf::Json& items, size_t n = 5) {
  if (!items.is_array()) {
    show(items);
    return;
  }
  std::cout << items.size() << " [";
  for (size_t i = 0; i < std::min(n, items.size()); ++i)
    std::cout << (i ? ", " : "") << "'" << (items[i].is_string() ? items[i].get<std::string>() : items[i].dump()) << "'";
  std::cout << "]\n";
}

//: Rows per (a, b) pair, rows with either one null left out: pandas' frame.groupby([a, b]).size().
inline void count_by(const lf::Table& table, const std::string& a, const std::string& b) {
  std::map<std::pair<std::string, std::string>, int64_t> counts;
  const auto left = table->GetColumnByName(a), right = table->GetColumnByName(b);
  for (int64_t i = 0; i < table->num_rows(); ++i) {
    const auto x = left->GetScalar(i).ValueOrDie(), y = right->GetScalar(i).ValueOrDie();
    if (x->is_valid && y->is_valid) ++counts[{x->ToString(), y->ToString()}];
  }
  for (const auto& [key, n] : counts) std::cout << key.first << "  " << key.second << "  " << n << "\n";
}

//: The sum of a numeric column (nulls skipped).
inline double column_sum(const lf::Table& table, const std::string& name) {
  double total = 0;
  const auto column = table->GetColumnByName(name);
  for (int64_t i = 0; i < column->length(); ++i) {
    const auto value = column->GetScalar(i).ValueOrDie();
    if (value->is_valid) total += std::static_pointer_cast<arrow::DoubleScalar>(value)->value;
  }
  return total;
}

//: Run an example: a server error is printed with its kind, as the Python client raises it.
template <typename Body>
int run(Body body) {
  try {
    body();
  } catch (const lf::RpcError& error) {
    std::cerr << (error.kind().empty() ? "RpcError" : error.kind()) << ": " << error.what() << "\n";
    return 1;
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
  return 0;
}
