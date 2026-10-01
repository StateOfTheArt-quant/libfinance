# libfinance C++ 客户端

与 Python 客户端（`python/`）逐一对应：同样的 27 个函数、同样的函数名、参数顺序与默认值、同样的
校验与报错、同样的答案（清单见 `contract/contract.json`，一致性由 `conformance/` 核对）。

```cpp
#include <libfinance/libfinance.hpp>
namespace lf = libfinance;

lf::init_client("127.0.0.1", 8080);                       // 不调用时连 LIBFINANCE_HOST:LIBFINANCE_PORT，
                                                          // 都没设则是 libfinance.tech:8080（生产环境）
auto found = lf::instruments("600000.XSHG", "2024-03-01");
lf::Table bars = lf::get_price({"000001.XSHE", "600000.XSHG"}, "2024-03-01", "2024-03-06");
auto days = lf::get_trading_dates("2024-03-01", "2024-03-31");
```

## 与 Python 版的类型对应

| Python | C++ |
|---|---|
| 日期（`str` / `date` / `int`） | `DateLike`：`"2024-03-01"`、`"20240301"`、`20240301`、`lf::Date` 都可以直接传 |
| 一个代码或代码列表 | `Codes`：`"600000.XSHG"` 或 `{"600000.XSHG", "AAPL.US"}`；`{}` / 省略即 `None` |
| 可选参数 `None` | `std::nullopt`（或省略） |
| `pandas.DataFrame` | `arrow::Table`（`lf::Table`）；Python 的索引列在 C++ 里是普通列，如 get_price 的 `order_book_id`、`datetime` |
| `DatetimeIndex` / `Timestamp` | `std::vector<lf::Date>` / `lf::Date` |
| `dict` | `nlohmann::json`（`lf::Json`） |
| `Instrument` | `lf::Instrument`；`instruments()` 在 C++ 里总是返回列表 |
| `ValueError` | `std::invalid_argument`（`CalendarCoverageError` 是它的子类） |
| 服务端返回的错误 | `lf::RpcError`：`code()`、`message()`、服务端给出的错误类别 `kind()` |
| `warnings.warn` | `lf::set_warning_handler(...)`，默认写到 stderr |

交易日历、`all_instruments` 的全表与 `get_price_coverage` 的缓存方式与 Python 版相同（日历按天、
其余按服务端 `ping` 报告的数据版本）。

## 构建

依赖：Arrow C++（conda 的 pyarrow 自带）与 lz4（`lz4frame.h`）。nlohmann/json、googletest 按模板的
`load_or_download_library` 取到 `third_party/`。客户端自己实现线上协议（`libfinance/src/wire.cpp`：帧、msgpack、
LZ4 帧，与 Python 的 `libfinance/client.py` 相同），不依赖服务端的任何库。

```bash
cmake -S cpp -B cpp/build -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DENABLE_UNITTEST=ON -DBUILD_EXAMPLES=ON
cmake --build cpp/build -j && (cd cpp/build && ctest)
cmake --install cpp/build --prefix <prefix>        # find_package(libfinance 0.1)
```

只要示例时，单独构建 `example/cpp` 即可，它用 FetchContent 取 libfinance（见那里的 CMakeLists.txt）。
用 conda 的 Arrow 在本机构建时，运行前加 `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6`（conda 的
libstdc++ 缺 `GLIBCXX_3.4.30`）。

## 布局

| 路径 | 是什么 |
|---|---|
| `libfinance/include/libfinance/` | 公开头文件，按 Python 的 `libfinance/api/*.py` 分：`calendar.hpp`、`instrument.hpp`、`price.hpp`…… |
| `libfinance/src/` | 实现；`client.cpp` 连接与解码，`internal.hpp` 参数校验与缓存（Python 的 `utils/`） |
| `tools/libfinance_call.cpp` | `libfinance-call <函数> '<JSON 参数>'`：按名调用任一函数，`conformance/` 用它 |
| `test/` | 离线单测：日期解析、`Codes`、两种表格编码的解码 |
| `../example/cpp/` | 示例，与 `../example/python/` 一一对应（`-DBUILD_EXAMPLES=ON`） |
