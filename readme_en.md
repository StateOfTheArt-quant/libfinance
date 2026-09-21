<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**A Python financial data interface for quantitative research and backtesting — A-shares · US equities**

[![PyPI](https://img.shields.io/pypi/v/libfinance?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/libfinance/)
[![docs en](https://img.shields.io/readthedocs/libfinance-en?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20en)](https://libfinance.readthedocs.io/en/latest/)
[![docs zh-cn](https://img.shields.io/readthedocs/libfinance?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20zh-cn)](https://libfinance.readthedocs.io/zh-cn/latest/)

[📗 English documentation](https://libfinance.readthedocs.io/en/latest/) ·
[📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) ·
[💻 Example scripts](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) ·
[🚀 Quickstart](https://libfinance.readthedocs.io/en/latest/getting_started/quickstart.html) ·
[🧭 Concepts](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html) ·
[📑 API reference](https://libfinance.readthedocs.io/en/latest/reference/contracts.html)

</div>

---

`libfinance` covers Chinese A-share and US equity markets. It provides prices, security information, trading calendars, corporate actions, financials, industry classifications, index and concept data, and live market data subscriptions. Query results fit naturally into pandas workflows.

Historical research needs clear security identities, information valid at the decision time, and consistent price conventions. These three requirements shape the data design:

- **Unified security identifiers** — `<trading_code>.<namespace>`, such as `600000.XSHG`, `000001.XSHE`, and `AAPL.US`, distinguishes codes across markets. Historical code resolution helps handle renaming and code reuse.
- **Point-in-time queries with `as_of`** — reconstruct historical security universes and select financial statement versions disclosed by the observation date, helping avoid look-ahead and survivorship bias.
- **High-quality adjustment factors, `exfactor`** — account for corporate actions when comparing prices, with unadjusted, forward-adjusted, and backward-adjusted series. Inspect event and cumulative factors through `get_ex_factor` to understand price adjustments.

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

For a line-by-line walkthrough of what these calls return, see the [quickstart](https://libfinance.readthedocs.io/en/latest/getting_started/quickstart.html).

## Three things to know first

These are not advanced topics — they are **defaults**. Miss them and the code still runs, but the numbers are wrong.

- **Without `adjust_type`, you get forward-adjusted prices.** For the same stock on the same day, the forward-adjusted close is 8.81 and the unadjusted close is 10.49 — a 16% difference. Select the convention explicitly with `adjust_type="none"` / `"pre"` / `"post"`; see [prices and adjustment](https://libfinance.readthedocs.io/en/latest/data/price.html).
- **`end_date` cannot be today.** The trading calendar is published ahead of time, while prices only reach the **last closed session**. Passing today as `end_date` is rejected explicitly rather than returning a shorter table; see [data freshness](https://libfinance.readthedocs.io/en/latest/data/freshness.html).
- **Financial statements get restated.** The same quarter's net profit is stored in several versions; without `as_of` in a backtest you are using numbers that did not exist yet. See [point-in-time financials](https://libfinance.readthedocs.io/en/latest/data/point_in_time.html).

## What data is here

| Data | Markets | Main function | Notes |
| --- | --- | --- | --- |
| Trading calendar | CN · US | `get_trading_dates` | Sessions, ranges, N sessions forward or back |
| Security master | CN · US | `all_instruments` | Code, name, type, listing and delisting dates |
| Daily bars | CN · US | `get_price` | OHLC, volume, turnover; adjustable |
| Adjustment factors | CN · US | `get_ex_factor` | Event and cumulative factors by ex-date |
| Share capital | CN | `get_shares` | Per-session total and floating shares |
| Dividends / splits / allotments | CN · US | `get_dividends` | Ex-rights events — the source of price gaps |
| Spinoffs | US | `get_spinoffs` | A-shares do not produce these events |
| Financial statements (PIT) | CN | `get_pit_financials_ex` | By quarter, with restatement history |
| Financial factors | CN | `get_factor` | Quarterly derived factors |
| Industry classification | CN | `get_industry_mapping` | Shenwan three-level taxonomy |
| Index constituents and weights | CN | `get_index_weights` | Constituent weights on any session |
| Concept board constituents | CN | `get_concept_weights` | THS concept taxonomy |
| Live quotes | CN | `QuoteApi` | Subscription push |

How far back the history goes and how current it is depend on the service you connect to. **Do not copy the dates from the documentation** — check them yourself with the two functions in [data freshness](https://libfinance.readthedocs.io/en/latest/data/freshness.html).

## Concepts

| Topic | What it solves |
| --- | --- |
| [Unified security identifiers](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html) | Distinguish markets, security identities, and historical codes to join data correctly |
| [Point-in-time queries with as_of](https://libfinance.readthedocs.io/en/latest/concepts/point_in_time.html) | Reconstruct historical universes and visible financial statements to avoid look-ahead and survivorship bias |
| [High-quality adjustment factors, exfactor](https://libfinance.readthedocs.io/en/latest/concepts/exfactor.html) | Understand corporate actions and the calculation and use of three price conventions |

## Documentation and examples

| | |
| --- | --- |
| [📗 English documentation](https://libfinance.readthedocs.io/en/latest/) | Concepts, data notes, how-to guides, and the API reference |
| [📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) | The same documentation tree in Chinese |
| [💻 Example scripts](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) | Runnable scripts for the six API groups, to read alongside the reference |
| [🧩 How-to guides](https://libfinance.readthedocs.io/en/latest/howto/index.html) | End-to-end recipes: price panels, PIT backtests, live subscriptions |
| [🩺 Troubleshooting](https://libfinance.readthedocs.io/en/latest/howto/troubleshooting.html) | Organized by **symptom**: start from the line that matches what you see |

The API reference groups functions into contracts and calendars, market data, fundamentals, industries and concepts, corporate actions, and live quotes. It includes parameter descriptions and scenario examples with printed output.

## Community

Questions and requests are welcome in [Issues](https://github.com/StateOfTheArt-quant/libfinance/issues). Follow us on WeChat for updates:

<div align="center">
    <img alt="WeChat QR code" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="600" height="220">
</div>
