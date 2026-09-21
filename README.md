<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**面向量化研究与回测的 Python 金融数据接口 —— A 股 · 美股**

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

`libfinance` 覆盖 A 股与美股，提供行情、证券信息、交易日历、公司行动、财务数据及行业、指数与概念数据，并支持实时行情订阅。查询结果便于直接用于 pandas 分析。

研究需要的不只是历史数字，还包括明确的证券身份、当时有效的信息，以及一致的价格口径。`libfinance` 把这三件事写进了数据设计：

- **统一的证券标识符** —— 用 `<trading_code>.<namespace>` 表达证券，例如 `600000.XSHG`、`000001.XSHE`、`AAPL.US`，区分不同市场的同名代码；结合历史时点解析代码，减少更名与代码复用带来的歧义。
- **point-in-time 机制 `as_of`** —— 按历史时点还原证券池，并选择当时已披露的财务版本，帮助避免未来信息和幸存者偏差。
- **高质量的复权因子 `exfactor`** —— 结合公司行动处理价格可比性，提供不复权、前复权和后复权行情；通过 `get_ex_factor` 查看单次及累计因子，让价格变化有据可查。

## 安装

```bash
pip install libfinance
```

从源码安装：

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance
pip install -e .
```

## 快速开始

按[安装与连接说明](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/installation.html)配置服务后，即可查询：

```python
from libfinance import instruments, get_price, get_ex_factor

# 查询历史时点对应的证券信息。
print(instruments("600000.XSHG", as_of="2024-03-01"))

# 显式选择不复权，查看历史原始行情。
print(get_price(
    ["000001.XSHE", "600000.XSHG"],
    "2024-03-01", "2024-03-06", adjust_type="none",
))

# 查看公司行动对应的单次及累计复权因子。
print(get_ex_factor("600000.XSHG", "2023-01-01", "2024-12-31"))
```

一分钟看懂这几行取到了什么，见[快速开始](https://libfinance.readthedocs.io/zh-cn/latest/getting_started/quickstart.html)。

## 数据覆盖

| 数据 | 市场 | 主要函数 | 说明 |
| --- | --- | --- | --- |
| 交易日历 | CN · US | `get_trading_dates` | 交易日、区间取日、前后推 N 个交易日 |
| 证券主数据 | CN · US | `all_instruments` | 代码、名称、类型、上市与退市日期 |
| 日频行情 | CN · US | `get_price` | 开高低收、成交量额，可复权 |
| 复权因子 | CN · US | `get_ex_factor` | 逐除权日的单次及累计因子 |
| 股本结构 | CN | `get_shares` | 逐交易日的总股本与流通股本 |
| 分红 / 拆股 / 配股 | CN · US | `get_dividends` | 除权事件，价格跳空的来源 |
| 分拆 | US | `get_spinoffs` | A 股不产生这类事件 |
| 财务报表（PIT） | CN | `get_pit_financials_ex` | 按季度取，带修订历史 |
| 财务因子 | CN | `get_factor` | 季度财务衍生因子 |
| 行业分类 | CN | `get_industry_mapping` | 申万三级分类 |
| 指数成分与权重 | CN | `get_index_weights` | 任意交易日的成分权重 |
| 概念板块成分 | CN | `get_concept_weights` | 同花顺概念分类 |
| 实时行情 | CN | `QuoteApi` | 订阅推送 |

覆盖到哪一年、更新到哪一天，取决于你连的那个服务。**不要照抄文档里的日期**，用[数据新鲜度](https://libfinance.readthedocs.io/zh-cn/latest/data/freshness.html)里的两个函数自己查。

## 概念设计

| 主题 | 解决的问题 |
| --- | --- |
| [统一的证券标识符](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html) | 区分市场、证券身份及历史代码，准确关联不同数据 |
| [point-in-time 机制 as_of](https://libfinance.readthedocs.io/zh-cn/latest/concepts/point_in_time.html) | 还原历史证券池与可见财报，避免未来信息和幸存者偏差 |
| [高质量的复权因子 exfactor](https://libfinance.readthedocs.io/zh-cn/latest/concepts/exfactor.html) | 理解公司行动对价格的影响，以及三种价格口径的计算和用途 |

## 文档与示例

| | |
| --- | --- |
| [📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) | 概念设计、数据说明、操作指南与 API 参考 |
| [📗 English documentation](https://libfinance.readthedocs.io/en/latest/) | The same documentation tree in English |
| [💻 示例代码](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) | 六类 API 的可运行脚本，与 API 参考对照阅读 |
| [🧩 操作指南](https://libfinance.readthedocs.io/zh-cn/latest/howto/index.html) | 取行情面板、PIT 回测、订阅实时行情等成套做法 |
| [🩺 故障排查](https://libfinance.readthedocs.io/zh-cn/latest/howto/troubleshooting.html) | 按**症状**编排：看到什么现象，就从哪一行开始 |

API 参考按合约信息和交易日历、行情信息、基本面信息、行业和概念信息、公司行动信息、实时行情分组，包含参数说明和带打印结果的场景示例。

## 社区

问题与需求请提 [Issue](https://github.com/StateOfTheArt-quant/libfinance/issues)。关注公众号获取更新：

<div align="center">
    <img alt="微信公众号二维码" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="600" height="220">
</div>
