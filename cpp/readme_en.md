# libfinance C++ client

[中文](README.md) · [Documentation](https://libfinance.readthedocs.io/en/latest/) · [Examples](../example/cpp)

## Background

`libfinance` is a financial data interface for quantitative research and backtesting. Chinese A-shares and
US equities share one vocabulary: the same security identifiers (`600000.XSHG`, `AAPL.US`), the same query
functions and arguments, and the same table structure. The data is served by the libfinance server and covers
prices, security information, trading calendars, corporate actions, share counts, financials, industries,
indices and themes; `as_of` reconstructs what was visible at a historical date, and adjustment factors keep
prices comparable over time.

The C++ client mirrors the Python client (`../python`) **one to one**: the same 30 functions, with the same
names, argument order and defaults, the same validation and errors, and the same answers. The function list is
`../contract/contract.json`; `../conformance/` checks that both languages agree. Use it where you want data
directly in C++ — a backtesting engine, factor computation, a trading system — without going through Python.
Both clients carry the repository's one version (`../VERSION`).

The client implements the wire protocol itself (`libfinance/src/wire.cpp`: frames, msgpack, LZ4 frames, as in
Python's `libfinance/client.py`) and depends on no server library.

```cpp
#include <libfinance/libfinance.hpp>
namespace lf = libfinance;

auto found = lf::instruments("600000.XSHG", "2024-03-01");      // the security as of that day
lf::Table bars = lf::get_price({"000001.XSHE", "600000.XSHG"}, "2024-03-01", "2024-03-06");
auto days = lf::get_trading_dates("2024-03-01", "2024-03-31");
```

## Using it in your C++ project (FetchContent)

### Prerequisites

- CMake ≥ 3.18 and a C++17 compiler
- [Apache Arrow C++](https://arrow.apache.org/install/): on Ubuntu, `libarrow-dev` from Apache's apt
  repository; or conda: `conda install -c conda-forge libarrow` (the one pyarrow ships also works)
- lz4 development files: `apt install liblz4-dev`, or conda's `lz4-c`

nlohmann/json need not be installed: the build fetches it (see below).

### CMakeLists.txt

Fetching libfinance and nlohmann/json as release tarballs is recommended — about 1 MB in total, no git, and a
fixed version:

```cmake
cmake_minimum_required(VERSION 3.18)
project(my_strategy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# nlohmann/json, declared first under this name: libfinance uses it instead of cloning the json repository.
# JSON_Install: libfinance exports its targets, and json's along with them.
set(JSON_Install ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
)

# Build only the library: not libfinance's tools, tests or examples.
set(BUILD_TOOLS     OFF CACHE BOOL "" FORCE)
set(BUILD_EXAMPLES  OFF CACHE BOOL "" FORCE)
set(ENABLE_UNITTEST OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    libfinance
    URL           https://github.com/StateOfTheArt-quant/libfinance/archive/refs/tags/v0.1.1.tar.gz
    SOURCE_SUBDIR cpp               # the C++ client lives in the repository's cpp/ directory
)
FetchContent_MakeAvailable(nlohmann_json libfinance)

add_executable(my_strategy main.cpp)
target_link_libraries(my_strategy PRIVATE libfinance::libfinance)
```

To change version, change the tag in the URL ([releases](https://github.com/StateOfTheArt-quant/libfinance/releases)).
Git works too (`GIT_REPOSITORY https://github.com/StateOfTheArt-quant/libfinance.git`, `GIT_TAG v0.1.1`,
`GIT_SHALLOW TRUE`, `SOURCE_SUBDIR cpp`, without the two nlohmann_json lines above): libfinance then clones
nlohmann/json itself, which takes considerably longer on a slow network. With a local libfinance checkout,
configure with `-DFETCHCONTENT_SOURCE_DIR_LIBFINANCE=<libfinance repository>` to skip the download.

### main.cpp

```cpp
#include <iostream>

#include <libfinance/libfinance.hpp>

namespace lf = libfinance;

int main() {
  for (const auto& day : lf::get_trading_dates("2024-03-01", "2024-03-08")) std::cout << day << " ";
  std::cout << "\n";

  lf::Table bars = lf::get_price({"600000.XSHG", "AAPL.US"}, "2024-03-01", "2024-03-06",
                                 /*frequency=*/"1d", /*fields=*/{"close", "volume"});
  std::cout << bars->ToString() << "\n";
}
```

### Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release     # add -DCMAKE_PREFIX_PATH=<Arrow prefix> if Arrow is not on a system path
cmake --build build -j
build/my_strategy
```

### Installing once and using find_package

To avoid recompiling libfinance in every project, install it once and find it as a package:

```bash
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=<Arrow prefix>
cmake --build cpp/build -j
cmake --install cpp/build --prefix <prefix>
```

```cmake
find_package(libfinance 0.1 REQUIRED)            # configure with -DCMAKE_PREFIX_PATH=<prefix>
target_link_libraries(my_strategy PRIVATE libfinance::libfinance)
```

If `<prefix>` is not a system path, run with `LD_LIBRARY_PATH=<prefix>/lib` (where `libfinance.so` is).

## Types, Python to C++

| Python | C++ |
|---|---|
| a date (`str` / `date` / `int`) | `DateLike`: `"2024-03-01"`, `"20240301"`, `20240301` or an `lf::Date` |
| one code or a list of codes | `Codes`: `"600000.XSHG"` or `{"600000.XSHG", "AAPL.US"}`; `{}` / omitted is `None` |
| an optional argument's `None` | `std::nullopt` (or omitted) |
| `pandas.DataFrame` | `arrow::Table` (`lf::Table`); Python's index columns are ordinary columns, e.g. get_price's `order_book_id`, `datetime` |
| `DatetimeIndex` / `Timestamp` | `std::vector<lf::Date>` / `lf::Date` |
| `dict` | `nlohmann::json` (`lf::Json`) |
| `Instrument` | `lf::Instrument`; `instruments()` always returns a list in C++ |
| `ValueError` | `std::invalid_argument` (`CalendarCoverageError` derives from it) |
| an error from the server | `lf::RpcError`: `code()`, `message()`, and the server's error kind `kind()` |
| `warnings.warn` | `lf::set_warning_handler(...)`; stderr by default |

The trading calendar, `all_instruments`' full table and `get_price_coverage` are cached as in Python (the
calendar per day, the others per data version reported by the server's `ping`).

## Development: building and testing in this repository

```bash
cmake -S cpp -B cpp/build -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DENABLE_UNITTEST=ON -DBUILD_EXAMPLES=ON
cmake --build cpp/build -j && (cd cpp/build && ctest)
```

The build fetches nlohmann/json and googletest into `third_party/`. When building against conda's Arrow, run
with `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6` (conda's libstdc++ lacks `GLIBCXX_3.4.30`).

## Layout

| Path | What it is |
|---|---|
| `libfinance/include/libfinance/` | public headers, split as Python's `libfinance/api/*.py`: `calendar.hpp`, `instrument.hpp`, `price.hpp`, ... |
| `libfinance/src/` | implementation; `client.cpp` connects and decodes, `internal.hpp` validates arguments and caches (Python's `utils/`) |
| `tools/libfinance_call.cpp` | `libfinance-call <function> '<JSON arguments>'`: calls any function by name; used by `conformance/` |
| `test/` | offline unit tests: date parsing, `Codes`, decoding both table encodings |
| `../example/cpp/` | examples, one per `../example/python/` script (`-DBUILD_EXAMPLES=ON`); the directory also builds on its own with FetchContent |
