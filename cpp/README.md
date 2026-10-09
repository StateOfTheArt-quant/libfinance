# libfinance C++ 客户端

[English](readme_en.md) · [中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) · [示例](../example/cpp)

## 背景

`libfinance` 是面向量化研究与回测的金融数据接口：A 股与美股用同一套术语——同样的证券标识
（`600000.XSHG`、`AAPL.US`）、同样的查询函数与参数、同样的表结构。数据由 libfinance 服务端提供，
覆盖行情、证券信息、交易日历、公司行动、股本、财务、行业、指数与主题；`as_of` 按历史时点还原当时
可见的信息，复权因子让价格前后可比。

C++ 客户端与 Python 客户端（`../python`）**逐一对应**：同样的 30 个函数、同样的函数名、参数顺序与
默认值、同样的校验与报错、同样的答案。函数清单见 `../contract/contract.json`，两种语言的一致性由
`../contract/conformance/` 核对。它适合需要在 C++ 里直接取数的场景——回测引擎、因子计算、实盘系统——不必经过
Python。两种客户端共用仓库的版本号（`../VERSION`）。

客户端自己实现线上协议（`libfinance/src/wire.cpp`：帧、msgpack、LZ4 帧，与 Python 的
`libfinance/client.py` 相同），不依赖服务端的任何库。

```cpp
#include <libfinance/libfinance.hpp>
namespace lf = libfinance;

auto found = lf::instruments("600000.XSHG", "2024-03-01");      // 当天有效的证券信息
lf::Table bars = lf::get_price({"000001.XSHE", "600000.XSHG"}, "2024-03-01", "2024-03-06");
auto days = lf::get_trading_dates("2024-03-01", "2024-03-31");
```

## 在自己的 C++ 项目里使用（FetchContent）

### 准备

- CMake ≥ 3.18，支持 C++17 的编译器
- [Apache Arrow C++](https://arrow.apache.org/install/)：Ubuntu 用 Apache 的 apt 源装 `libarrow-dev`；
  或 conda：`conda install -c conda-forge libarrow`（pyarrow 自带的也可以）
- lz4 开发包：`apt install liblz4-dev`，或 conda 的 `lz4-c`

nlohmann/json 不必预装：由构建取得（见下）。

### CMakeLists.txt

推荐从发布的源码包取 libfinance 与 nlohmann/json——只下载约 1 MB，不需要 git，版本固定：

```cmake
cmake_minimum_required(VERSION 3.18)
project(my_strategy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# nlohmann/json：先以同名声明，libfinance 就用它，不再克隆 json 仓库。
# JSON_Install：libfinance 导出自己的 target 时要连同 json 的一起导出。
set(JSON_Install ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
)

# 只构建库：不要 libfinance 的工具、单测与示例。
set(BUILD_TOOLS     OFF CACHE BOOL "" FORCE)
set(BUILD_EXAMPLES  OFF CACHE BOOL "" FORCE)
set(ENABLE_UNITTEST OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    libfinance
    URL           https://github.com/StateOfTheArt-quant/libfinance/archive/refs/tags/v0.1.1.tar.gz
    SOURCE_SUBDIR cpp               # C++ 客户端在仓库的 cpp/ 目录
)
FetchContent_MakeAvailable(nlohmann_json libfinance)

add_executable(my_strategy main.cpp)
target_link_libraries(my_strategy PRIVATE libfinance::libfinance)
```

换版本只改 URL 里的标签（[发布列表](https://github.com/StateOfTheArt-quant/libfinance/releases)）。
也可以用 git 取（`GIT_REPOSITORY https://github.com/StateOfTheArt-quant/libfinance.git`、`GIT_TAG v0.1.1`、
`GIT_SHALLOW TRUE`、`SOURCE_SUBDIR cpp`，并去掉上面 nlohmann_json 的两段）：此时 libfinance 自己克隆
nlohmann/json，网络慢时要多花不少时间。本地已有 libfinance 源码时，配置时传
`-DFETCHCONTENT_SOURCE_DIR_LIBFINANCE=<libfinance 仓库>` 即可不下载。

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

### 构建与运行

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release     # Arrow 不在系统路径时加 -DCMAKE_PREFIX_PATH=<Arrow 的安装前缀>
cmake --build build -j
build/my_strategy
```

### 安装后用 find_package

不想在每个项目里重新编译时，装一次 libfinance，之后按包查找：

```bash
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=<Arrow 的安装前缀>
cmake --build cpp/build -j
cmake --install cpp/build --prefix <prefix>
```

```cmake
find_package(libfinance 0.1 REQUIRED)            # 配置时 -DCMAKE_PREFIX_PATH=<prefix>
target_link_libraries(my_strategy PRIVATE libfinance::libfinance)
```

`<prefix>` 不是系统路径时，运行前设 `LD_LIBRARY_PATH=<prefix>/lib`（`libfinance.so` 在那里）。

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

## 开发：在本仓库里构建与测试

```bash
cmake -S cpp -B cpp/build -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DENABLE_UNITTEST=ON -DBUILD_EXAMPLES=ON
cmake --build cpp/build -j && (cd cpp/build && ctest)
```

nlohmann/json、googletest 由构建取到 `third_party/`。用 conda 的 Arrow 在本机构建时，运行前加
`LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6`（conda 的 libstdc++ 缺 `GLIBCXX_3.4.30`）。

## 布局

| 路径 | 是什么 |
|---|---|
| `libfinance/include/libfinance/` | 公开头文件，按 Python 的 `libfinance/api/*.py` 分：`calendar.hpp`、`instrument.hpp`、`price.hpp`…… |
| `libfinance/src/` | 实现；`client.cpp` 连接与解码，`internal.hpp` 参数校验与缓存（Python 的 `utils/`） |
| `tools/libfinance_call.cpp` | `libfinance-call <函数> '<JSON 参数>'`：按名调用任一函数，`contract/conformance/` 用它 |
| `test/` | 离线单测：日期解析、`Codes`、两种表格编码的解码 |
| `../example/cpp/` | 示例，与 `../example/python/` 一一对应（`-DBUILD_EXAMPLES=ON`）；该目录也可单独用 FetchContent 构建 |
