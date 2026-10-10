<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**面向量化研究与回测的金融数据接口 —— A 股与美股一套术语，Python 与 C++ 一套函数**

[![PyPI](https://img.shields.io/pypi/v/libfinance?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/libfinance/)
[![docs zh-cn](https://img.shields.io/readthedocs/libfinance?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20zh-cn)](https://libfinance.readthedocs.io/zh-cn/latest/)
[![docs en](https://img.shields.io/readthedocs/libfinance-en?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20en)](https://libfinance.readthedocs.io/en/latest/)

[📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) ·
[📗 English documentation](https://libfinance.readthedocs.io/en/latest/) ·
[💻 示例代码](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) ·
[🚀 快速开始](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/quickstart.html) ·
[🧭 概念设计](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html) ·
[📑 API 参考](https://libfinance.readthedocs.io/zh-cn/latest/reference/contracts.html)

</div>

---

`libfinance` 是面向量化研究与回测的金融数据客户端，有 Python 与 C++ 两种实现，覆盖 A 股与美股。

代码本身带着市场（`600000.XSHG`、`AAPL.US`），同一次调用可以混查两个市场。函数、参数和返回的表结构在两个市场之间完全相同，差别只在数据里：例如美股没有涨跌停价，`limit_up` 一列为 `NaN`。

数据包括日线行情与复权因子、证券目录、交易日历、分红拆股等公司行动、股本、财务报表与衍生指标、行业 / 指数 / 主题的成分与权重、日频因子（alpha158、qlib、Barra），以及 A 股实时行情。表格结果在 Python 中是 `pandas.DataFrame`，在 C++ 中是 `arrow::Table`，列名相同。

回测结果是否可信，取决于证券身份是否准确、所用信息当时是否已经可得、价格口径是否一致。数据设计有四条约定：

- **统一的证券标识符** —— `<trading_code>.<namespace>`，如 `600000.XSHG`、`000001.XSHE`、`AAPL.US`。命名空间区分不同市场的同号代码，代码按历史时点解析，更名与代码复用不会串到别的证券。
- **point-in-time 机制 `as_of`** —— 按历史时点还原证券池、选取当时已披露的财务版本，避免未来信息与幸存者偏差。
- **高质量的复权因子 `exfactor`** —— 由公司行动逐事件计算，提供不复权、前复权、后复权三种口径；`get_ex_factor` 给出单次与累计因子，价格的每一次调整都可追溯。
- **Python 与 C++ 统一的函数设计** —— 两种客户端按同一份契约（`contract/contract.json`）实现，函数名、参数顺序与默认值、校验与报错、返回的列一一对应；同一组调用经两种客户端发给同一服务端逐项比对。

## 安装

```bash
pip install libfinance
```

从源码安装：

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance/python
pip install -e .
```

> [!TIP]
> **使用 C++？** C++ 客户端与 Python 版函数一一对应，通过 CMake `FetchContent` 引入项目，依赖 Apache Arrow C++。安装、构建与示例见 [cpp/README.md](https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/README.md)。

## 快速开始

按[安装与连接说明](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/installation.html)配置服务后即可查询。以下输出均为真实运行结果，数据持续更新，行数与数值可能不同。

**证券目录** —— 两个市场在同一张表里，列相同：

```python
from libfinance import all_instruments

stocks = all_instruments(type="stock")
stocks.set_index("order_book_id").loc[
    ["600000.XSHG", "000001.XSHE", "AAPL.US", "NVDA.US"], ["market", "exchange", "name"]]
```

```text
              market exchange                               name
order_book_id
600000.XSHG       CN     XSHG                               浦发银行
000001.XSHE       CN     XSHE                               平安银行
AAPL.US           US     XNAS          Apple Inc. - Common Stock
NVDA.US           US     XNAS  NVIDIA Corporation - Common Stock
```

**交易日** —— 区间按自然日给，返回其中的交易日（美股传 `market="us"`）：

```python
from libfinance import get_trading_dates

get_trading_dates("2024-05-11", "2024-05-20")
```

```text
DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
               '2024-05-17', '2024-05-20'],
              dtype='datetime64[us]', freq=None)
```

**行情** —— 一次调用混查两个市场；美股没有涨跌停，`limit_up` 为 `NaN`，表结构不变：

```python
from libfinance import get_price

get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05",
          fields=["open", "close", "volume", "limit_up"], adjust_type="none")
```

```text
                            open   close    volume  limit_up
order_book_id datetime
600000.XSHG   2024-03-01    7.13    7.11  29431801      7.87
              2024-03-04    7.12    7.07  27855963      7.82
              2024-03-05    7.05    7.16  41756232      7.78
AAPL.US       2024-03-01  179.55  179.66  73563100       NaN
              2024-03-04  176.15  175.10  81510101       NaN
              2024-03-05  170.76  170.12  95132400       NaN
```

`adjust_type="none"` 取当天的真实成交价；不传时默认前复权（`"pre"`），见[价格口径](https://libfinance.readthedocs.io/zh-cn/latest/data/price.html)。

**因子** —— 库名 `system/alpha158` 展开为 158 个因子，每个因子一列：

```python
from libfinance import get_factor_exposure

f = get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158", "2026-09-07", "2026-09-10")
f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(4)   # 前 6 列，列名只留因子名
```

```text
                            KMID    KLEN   KMID2     KUP    KUP2    KLOW
order_book_id date
600000.XSHG   2026-09-07 -0.0212  0.0286 -0.7407  0.0032  0.1111  0.0042
              2026-09-08  0.0076  0.0141  0.5385  0.0065  0.4615  0.0000
              2026-09-09 -0.0022  0.0086 -0.2500  0.0043  0.5000  0.0022
              2026-09-10  0.0141  0.0184  0.7647  0.0011  0.0588  0.0033
000001.XSHE   2026-09-07 -0.0143  0.0194 -0.7391  0.0008  0.0435  0.0042
              2026-09-08  0.0103  0.0137  0.7500  0.0026  0.1875  0.0009
              2026-09-09 -0.0051  0.0085 -0.6000  0.0026  0.3000  0.0009
              2026-09-10  0.0146  0.0171  0.8500  0.0009  0.0500  0.0017
```

逐步说明见[快速开始](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/quickstart.html)。

## A 股与美股共用一套术语

统一体现在三个层面。

| 层面 | 统一的内容 | 例 |
| --- | --- | --- |
| 证券标识 | 写法都是 `<trading_code>.<namespace>`；命名空间的粒度取决于该市场消除歧义所需的范围 | `600000.XSHG`、`AAPL.US` |
| 函数与参数 | 两个市场调用同一组函数，参数名相同，`as_of` 与 `adjust_type` 的含义一致 | `get_price`、`instruments`、`get_dividends` |
| 返回结构 | 列名与索引一致；某个市场不适用或未提供的字段取 `NaN`，不另设一张表 | 美股的 `turnover`、`limit_up`、`limit_down` |

需要显式指定市场的，只有不涉及具体证券的查询：交易日历、全市场目录、数据覆盖范围。按证券查询时，命名空间已经给出了市场信息，列表里也可以混合两个市场的代码。

```python
from libfinance import instruments, get_trading_dates

instruments(["000001.XSHE", "AAPL.US"])                      # 命名空间已给出市场
get_trading_dates("2024-01-01", "2024-01-31", market="us")   # 不涉及具体证券
```

统一的是术语和调用约定，数据本身的差异依然存在。下表的「市场」一列标出了每类数据实际覆盖的市场，逐个接口的情况见[查美股](https://libfinance.readthedocs.io/zh-cn/latest/howto/us_market.html)。

## 数据覆盖

| 数据 | 市场 | 主要函数 | 说明 |
| --- | --- | --- | --- |
| 交易日历 | CN · US | `get_trading_dates` | 交易日、区间取日、前后推 N 个交易日 |
| 证券目录 | CN · US | `all_instruments`、`instruments` | 股票、指数、行业、主题；代码、名称、上市与退市日期 |
| 日频行情 | CN · US | `get_price` | 开高低收、成交量额、涨跌停价，可复权 |
| 复权因子 | CN · US | `get_ex_factor` | 逐除权日的单次及累计因子 |
| 股本 | CN · US | `get_shares` | 逐交易日的总股本与流通股本 |
| 分红 / 拆股 / 配股 | CN · US | `get_dividends`、`get_splits`、`get_allotments` | 除权事件；配股只有 A 股 |
| 分拆 | US | `get_spinoffs` | A 股不产生这类事件 |
| 财务报表（PIT） | CN · US | `get_pit_financials_ex` | 按季度取，带修订历史 |
| 财务衍生指标 | CN · US | `get_financial_metrics` | 按交易日的财务衍生指标 |
| 行业分类 | CN · US | `get_instrument_industry`、`get_industry_constituents`、`get_industry_weights` | 申万、GICS 等分类体系 |
| 指数成分与权重 | CN · US | `get_index_constituents`、`get_index_weights` | 中证、标普等 |
| 主题成分与权重 | CN | `get_theme_constituents`、`get_theme_weights` | THS 主题 |
| 日频因子 | CN | `get_factor_exposure`、`list_factor_libraries`、`list_factors` | alpha158、qlib、Barra CNE5 / CNE6 |
| 实时行情 | CN | `get_last_quotes`、`QuoteApi` | 最新快照与订阅推送 |

覆盖到哪一年、更新到哪一天，取决于你连的那个服务。**不要照抄文档里的日期**，用[数据新鲜度](https://libfinance.readthedocs.io/zh-cn/latest/data/freshness.html)里的两个函数自己查。

## 概念设计

| 主题 | 解决的问题 |
| --- | --- |
| [统一的证券标识符](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html) | 区分市场、证券身份及历史代码，准确关联不同数据 |
| [point-in-time 机制 as_of](https://libfinance.readthedocs.io/zh-cn/latest/concepts/point_in_time.html) | 还原历史证券池与可见财报，避免未来信息和幸存者偏差 |
| [高质量的复权因子 exfactor](https://libfinance.readthedocs.io/zh-cn/latest/concepts/exfactor.html) | 理解公司行动对价格的影响，以及三种价格口径的计算和用途 |
| [Python 与 C++ 统一的函数设计](https://libfinance.readthedocs.io/zh-cn/latest/concepts/python_cpp.html) | 一份契约约束两种客户端：函数、参数、报错与返回列一一对应，并逐项核对 |

## 文档与示例

| | |
| --- | --- |
| [📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) | 概念设计、数据说明、操作指南与 API 参考 |
| [📗 English documentation](https://libfinance.readthedocs.io/en/latest/) | The same documentation tree in English |
| [💻 示例代码](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) | 按数据族排序的可运行示例（Python 与 C++ 一一对应），与 API 参考对照阅读 |
| [🧩 操作指南](https://libfinance.readthedocs.io/zh-cn/latest/howto/index.html) | 取行情面板、PIT 回测、订阅实时行情等成套做法 |
| [🩺 故障排查](https://libfinance.readthedocs.io/zh-cn/latest/howto/troubleshooting.html) | 按**症状**编排：看到什么现象，就从哪一行开始 |

API 参考按合约信息和交易日历、行情、基本面、行业与指数和主题、公司行动、实时行情、因子分组，每个函数附 Python 与 C++ 两种写法的示例及其真实输出。

## 社区

问题与需求请提 [Issue](https://github.com/StateOfTheArt-quant/libfinance/issues)。关注公众号获取更新：

<div align="center">
    <img alt="微信公众号二维码" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="600" height="220">
</div>

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `contract/` | 各语言客户端共同遵守的契约：公开函数（名称、参数顺序与默认值、返回）与它们调用的服务端函数 |
| `contract/conformance/` | 同一组调用分别经 Python 与 C++ 客户端发给同一个服务端，逐项比对答案 |
| `python/` | Python 客户端（PyPI 上的 `libfinance`） |
| `cpp/` | C++ 客户端 |
| `docs/` | 文档（中英双语） |
