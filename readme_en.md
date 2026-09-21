# libfinance

[[中文](README.md) | English]

`libfinance` is a Python financial data interface for quantitative research and backtesting across Chinese A-share and US equity markets. It provides prices, security information, trading calendars, corporate actions, financials, industry classifications, index and concept data, and live market data subscriptions. Query results fit naturally into pandas workflows.

Historical research needs clear security identities, information valid at the decision time, and consistent price conventions. These requirements shape the data design:

- **Unified security identifiers**: `<trading_code>.<namespace>`, such as `600000.XSHG`, `000001.XSHE`, and `AAPL.US`, distinguishes codes across markets. Historical code resolution helps handle renaming and code reuse.
- **Point-in-time queries with `as_of`**: reconstruct historical security universes and select financial statement versions disclosed by the observation date, helping avoid look-ahead and survivorship bias.
- **High-quality adjustment factors, `exfactor`**: account for corporate actions when comparing prices, with unadjusted, forward-adjusted, and backward-adjusted series. Inspect event and cumulative factors through `get_ex_factor` to understand price adjustments.

## Install

```bash
pip install libfinance
```

From source:

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance
pip install -e .
```

## Quick start

Configure your connection using the [installation guide](https://libfinance.readthedocs.io/en/latest/getting_started/installation.html), then query:

```python
from libfinance import instruments, get_price, get_ex_factor

# Resolve security information at a historical observation date.
print(instruments("600000.XSHG", as_of="2024-03-01"))

# Select unadjusted prices explicitly for historical market prices.
print(get_price(
    ["000001.XSHE", "600000.XSHG"],
    "2024-03-01", "2024-03-06", adjust_type="none",
))

# Inspect event and cumulative adjustment factors.
print(get_ex_factor("600000.XSHG", "2023-01-01", "2024-12-31"))
```

`get_price` defaults to forward-adjusted prices. Use `adjust_type="none"`, `"pre"`, or `"post"` to select the convention explicitly. Available dates and coverage depend on the connected service.

## Concepts and documentation

| Topic | What it solves |
| --- | --- |
| [Unified security identifiers](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html) | Distinguish markets, security identities, and historical codes to join data correctly |
| [Point-in-time queries with as_of](https://libfinance.readthedocs.io/en/latest/concepts/point_in_time.html) | Reconstruct historical universes and visible financial statements to avoid look-ahead and survivorship bias |
| [High-quality adjustment factors, exfactor](https://libfinance.readthedocs.io/en/latest/concepts/exfactor.html) | Understand corporate actions and the calculation and use of three price conventions |

[English documentation](https://libfinance.readthedocs.io/en/latest/) · [中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) · [Example scripts](example/)

The API reference groups functions into contracts and calendars, market data, fundamentals, industries and concepts, corporate actions, and live quotes. It includes parameter descriptions and scenario examples with printed output.

## Community

Follow us on WeChat for updates:

<div>
    <img alt="WeChat QR code" src="docs/_shared/_static/img/code.png" width="600" height="220">
</div>
