# libfinance

[中文 | [English](readme_en.md)]

`libfinance` 是面向量化研究与回测的 Python 金融数据接口，覆盖 A 股与美股，提供行情、证券信息、交易日历、公司行动、财务数据及行业、指数与概念数据，并支持实时行情订阅。查询结果便于直接用于 pandas 分析。

研究需要的不只是历史数字，还包括明确的证券身份、当时有效的信息，以及一致的价格口径。`libfinance` 将这些要求融入数据设计：

- **统一的证券标识符**：使用 `<trading_code>.<namespace>` 表达证券，例如 `600000.XSHG`、`000001.XSHE` 和 `AAPL.US`，区分不同市场的同名代码；结合历史时点解析代码，减少更名与代码复用带来的歧义。
- **point-in-time 机制 `as_of`**：按历史时点还原证券池，并选择当时已披露的财务版本，帮助避免未来信息和幸存者偏差。
- **高质量的复权因子 `exfactor`**：结合公司行动处理价格可比性，提供不复权、前复权和后复权行情；通过 `get_ex_factor` 查看单次及累计因子，让价格变化有据可查。

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

`get_price` 默认返回前复权行情；通过 `adjust_type="none"`、`"pre"` 或 `"post"` 明确选择口径。可查询日期和数据范围以所连接服务的覆盖为准。

## 概念设计与文档

| 主题 | 解决的问题 |
| --- | --- |
| [统一的证券标识符](https://libfinance.readthedocs.io/zh-cn/latest/concepts/security_identifiers.html) | 区分市场、证券身份及历史代码，准确关联不同数据 |
| [point-in-time 机制 as_of](https://libfinance.readthedocs.io/zh-cn/latest/concepts/point_in_time.html) | 还原历史证券池与可见财报，避免未来信息和幸存者偏差 |
| [高质量的复权因子 exfactor](https://libfinance.readthedocs.io/zh-cn/latest/concepts/exfactor.html) | 理解公司行动对价格的影响，以及三种价格口径的计算和用途 |

[中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) · [English documentation](https://libfinance.readthedocs.io/en/latest/) · [示例代码](example/)

API 参考按合约信息和交易日历、行情信息、基本面信息、行业和概念信息、公司行动信息、实时行情分组，包含参数说明和带打印结果的场景示例。

## 社区

关注公众号获取更新：

<div>
    <img alt="微信公众号二维码" src="docs/_shared/_static/img/code.png" width="600" height="220">
</div>
