<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**面向量化研究与回测的 Python 金融数据客户端，A 股与美股共用一套调用约定**

[![PyPI](https://img.shields.io/pypi/v/libfinance?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/libfinance/)
[![docs zh-cn](https://img.shields.io/readthedocs/libfinance?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20zh-cn)](https://libfinance.readthedocs.io/zh-cn/latest/)
[![docs en](https://img.shields.io/readthedocs/libfinance-en?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20en)](https://libfinance.readthedocs.io/en/latest/)

[中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) ·
[English](https://github.com/StateOfTheArt-quant/libfinance/blob/main/readme_en.md) ·
[示例脚本](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) ·
[引用](#引用)

</div>

---

## 概述

`libfinance` 是一个轻量的 Python 客户端。数据存放在服务端，客户端负责发起查询，并把结果整理成 pandas 的 `DataFrame` 或 `Series`。覆盖交易日历、证券主数据、日频行情、复权因子、公司行动、财务报表、行业、指数与概念成分，以及 A 股实时行情订阅。

A 股与美股使用同一组函数、同样的参数名和同样的返回结构。两个市场的差异体现在数据本身（例如美股没有涨跌停），而不是调用方式上。

## 设计要点

历史研究里最常见的错误，往往不是价格取错了，而是对象、时点或口径没有对齐。本库在数据层面处理下面三件事。

**证券身份。** 单独的 `000001` 既可以指上证综合指数，也可以指平安银行。本库统一使用 `<trading_code>.<namespace>`（在 API 中称为 `order_book_id`），例如 `000001.XSHG`、`000001.XSHE`、`AAPL.US`。代码也有有效期：更名或代码复用之后，同一个代码在不同年份可能指向不同的公司，因此 `instruments` 可以结合 `as_of` 按历史时点解析。
→ [统一的证券标识符](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html)

**观察时点 `as_of`。** 财报的报告期和披露日是两回事，披露之后还可能被追溯修订。例如 `000016.XSHE` 2023 年年报的净利润在库里有 6 个版本，最后一版发布于 2026 年 4 月，亏损从 26.36 亿修订为 27.30 亿。2024 年的回测如果用了这个数字，就用上了当时还不存在的信息。`as_of` 让查询显式带上观察时点：财务数据只返回该时点以前已披露的版本，证券池按当时的上市状态重建，把后来退市的证券放回历史，以避免幸存者偏差。
→ [point-in-time 机制 as_of](https://libfinance.readthedocs.io/zh-cn/latest/concepts/point_in_time.html)

**价格口径。** 派现、送股、配股会让价格出现机械性的跳变，这些跳变不代表投资损益。本库按 `PRIOR_CLOSE` 口径计算复权因子：单次因子等于除权前收盘价除以理论除权价，累计因子是除权日以前各次因子的乘积。行情可按不复权、前复权、后复权三种口径返回，每个除权日的单次与累计因子都可以通过 `get_ex_factor` 查到并逐一核对。需要注意，这一口径与"乘到历史价格上的调整系数"互为倒数，和其他数据源比对前应先确认方向。
→ [复权因子 exfactor](https://libfinance.readthedocs.io/zh-cn/latest/concepts/exfactor.html)

## 安装与连接

需要 Python 3.7 或更高版本。

```bash
pip install libfinance
```

或从源码安装：

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance
pip install -e .
```

`import libfinance` 本身不会建立连接，第一次调用查询函数时才会连接服务端。默认地址是 `libfinance.tech:8080`。如果要连到其他服务（例如本地部署），可以用下面两种方式之一：

```bash
# 方式一：环境变量，必须在 import libfinance 之前设置
export LIBFINANCE_HOST=127.0.0.1
export LIBFINANCE_PORT=8080
```

```python
# 方式二：在第一次查询前显式初始化
from libfinance import init_client
init_client(host="127.0.0.1", port=8080)
```

## 最小示例

```python
from libfinance import instruments, get_price, get_ex_factor

# 按历史时点解析证券信息
print(instruments("600000.XSHG", as_of="2024-03-01"))

# 显式指定不复权，得到历史上的实际成交价
print(get_price(
    ["000001.XSHE", "600000.XSHG"],
    "2024-03-01", "2024-03-06", adjust_type="none",
))

# 查看每个除权日的单次与累计复权因子
print(get_ex_factor("600000.XSHG", "2023-01-01", "2024-12-31"))
```

`get_price` 返回的 `DataFrame` 以 `(order_book_id, datetime)` 为两层索引。取单只证券用 `df.loc["000001.XSHE"]`，取某一天用 `df.xs("2024-03-04", level="datetime")`。每一行输出的含义见[快速开始](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/quickstart.html)。

## 使用前需要知道的默认行为

下面几点不属于高级用法，而是默认行为。不了解它们，代码照样能运行，但得到的数字可能是错的。

1. **不传 `adjust_type` 时，`get_price` 返回的是前复权价。** 以 `000001.XSHE` 在 2024-03-01 为例，前复权收盘价是 8.81，当天的实际成交价是 10.49。需要实际成交价时，请写 `adjust_type="none"`。该默认值在 0.0.6 版从 `"none"` 改为 `"pre"`，依赖旧行为的代码需要显式指定，详见[变更记录](https://libfinance.readthedocs.io/zh-cn/latest/about/changelog.html)。
2. **行情只更新到最后一个已收盘并完成入库的交易日。** 交易日历会提前排到年底，行情却不会。`end_date` 超出行情覆盖范围时，会先给出警告，随后报错，不会悄悄返回一张更短的表。覆盖边界请用 `get_price_coverage()` 和 `get_calendar_coverage()` 查询，不要照抄文档里的日期。
3. **回测中查询财务数据时，请传入 `as_of`。** 不传的话，拿到的是截至今天的最新修订版。

## 数据覆盖

| 数据 | 市场 | 主要函数 | 说明 |
| --- | --- | --- | --- |
| 交易日历 | CN · US | `get_trading_dates` | 交易日、区间取日、前后推 N 个交易日 |
| 证券主数据 | CN · US | `all_instruments`、`instruments` | 代码、名称、类型、上市与退市日期 |
| 日频行情 | CN · US | `get_price` | 开高低收、成交量、成交额，可复权 |
| 复权因子 | CN · US | `get_ex_factor` | 逐除权日的单次与累计因子 |
| 股本结构 | CN | `get_shares` | 逐交易日的总股本与流通股本 |
| 分红 / 拆股 / 配股 | CN · US | `get_dividends`、`get_splits`、`get_allotments` | 除权事件，也是价格跳空的来源 |
| 分拆 | US | `get_spinoffs` | A 股没有这类事件 |
| 财务报表（PIT） | CN | `get_pit_financials_ex` | 按季度查询，保留修订历史 |
| 财务因子 | CN | `get_factor` | 由季度财务数据衍生的因子 |
| 行业分类 | CN | `get_industry_mapping` | 申万三级分类 |
| 指数成分与权重 | CN | `get_index_weights` | 任一交易日的成分与权重 |
| 概念板块成分 | CN | `get_concept_weights` | 同花顺概念分类 |
| 实时行情 | CN | `QuoteApi` | 订阅推送 |

按证券查询时，市场由代码的命名空间决定，同一个列表里可以混合两个市场的代码。只有不针对具体证券的查询（交易日历、全市场目录、覆盖范围）需要显式传入 `market`。某个市场不适用或未提供的字段返回 `NaN`，表结构保持不变。

```python
from libfinance import instruments, get_trading_dates

instruments(["000001.XSHE", "AAPL.US"])                      # 命名空间已经给出市场
get_trading_dates("2024-01-01", "2024-01-31", market="us")   # 不涉及具体证券
```

## 范围与局限

- 行情目前只支持日频（`frequency="1d"`），不提供分钟线和逐笔数据。
- 股本、财务、行业、指数成分、概念成分和实时行情目前只覆盖 A 股。美股没有涨跌停字段，部分部署也没有美股成交额。逐个接口的情况见[查美股](https://libfinance.readthedocs.io/zh-cn/latest/howto/us_market.html)。
- 数据的起止日期取决于所连接的服务，文档中的日期仅作示例。
- 项目仍处于 0.x 阶段，接口可能调整（例如 `get_index_weights` 的 `index_id` 已改为 `index_code`）。所有会改变已有代码行为的变更都记录在[变更记录](https://libfinance.readthedocs.io/zh-cn/latest/about/changelog.html)中。

## 文档

- [快速开始](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/quickstart.html)：交易日、标的、行情，一条完整的查询链路
- [概念设计](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html)：证券标识符、point-in-time、复权因子
- [数据说明](https://libfinance.readthedocs.io/zh-cn/latest/data/index.html)：每一类数据的口径与更新情况
- [操作指南](https://libfinance.readthedocs.io/zh-cn/latest/howto/index.html)：行情面板、PIT 回测、收益率计算、实时订阅
- [API 参考](https://libfinance.readthedocs.io/zh-cn/latest/reference/contracts.html)：参数说明，附带打印结果的示例
- [故障排查](https://libfinance.readthedocs.io/zh-cn/latest/howto/troubleshooting.html)：按遇到的现象查找原因
- [示例脚本](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example)：与 API 参考六个分组对应的可运行脚本

英文文档：<https://libfinance.readthedocs.io/en/latest/>

## 引用

如果 `libfinance` 对你的研究有帮助，可以按如下方式引用：

```bibtex
@misc{libfinance,
  author       = {Yu Jiang},
  title        = {libfinance: a python library for accessing high quality finance data},
  year         = {2024},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/StateOfTheArt-quant/libfinance}},
}
```

## 维护与反馈

本项目由 StateOfTheArt.Quant 维护，核心贡献者为 Yu Jiang（[@walkacross](https://github.com/walkacross)）。发现数据口径问题、缺陷或有新需求时，欢迎提交 [Issue](https://github.com/StateOfTheArt-quant/libfinance/issues)。附上调用代码与实际输出，能帮助我们更快定位问题。

项目更新也会发布在微信公众号：

<div align="center">
    <img alt="微信公众号二维码" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="300">
</div>
