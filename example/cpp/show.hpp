// What the examples print, and how they run: the C++ counterpart of the Python examples' print().
#pragma once

#include <iostream>
#include <string>
#include <vector>

#include <arrow/api.h>

#include <libfinance/libfinance.hpp>

namespace lf = libfinance;

//: A table: its first rows (all of them when `rows` is 0).
inline void show(const lf::Table& table, int64_t rows = 5) {
  if (!table) {
    std::cout << "(none)\n";
    return;
  }
  const auto shown = rows > 0 && table->num_rows() > rows ? table->Slice(0, rows) : table;
  std::cout << shown->ToString() << "(" << table->num_rows() << " rows)\n";
}

inline void show(const lf::Json& value) { std::cout << value.dump(2) << "\n"; }

inline void show(const std::vector<lf::Date>& dates) {
  std::cout << "[";
  for (size_t i = 0; i < dates.size(); ++i) std::cout << (i ? ", " : "") << dates[i];
  std::cout << "] (" << dates.size() << " days)\n";
}

inline void show(lf::Date date) { std::cout << date << "\n"; }
inline void show(bool value) { std::cout << (value ? "true" : "false") << "\n"; }
inline void show(int value) { std::cout << value << "\n"; }

inline void show(const std::vector<lf::Instrument>& found) {
  for (const auto& instrument : found) std::cout << instrument.fields().dump() << "\n";
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
