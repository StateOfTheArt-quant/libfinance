<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**A financial data interface for quantitative research and backtesting — one vocabulary for A-shares and US equities, one set of functions for Python and C++**

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

`libfinance` is a financial data client for quantitative research and backtesting, implemented in Python and in C++, covering Chinese A-shares and US equities.

A code carries its market (`600000.XSHG`, `AAPL.US`), so one call can mix both markets. Functions, arguments and returned tables are the same for the two markets; they differ only in their data — US stocks have no price limits, so their `limit_up` column is `NaN`.

The data covers daily bars and adjustment factors, the security catalog, trading calendars, corporate actions such as dividends and splits, shares outstanding, financial statements and derived metrics, industry / index / theme constituents and weights, daily factors (alpha158, qlib, Barra), and live A-share quotes. Tables are `pandas.DataFrame` in Python and `arrow::Table` in C++, with the same column names.

A backtest can be trusted only if each security is identified correctly, each input was available at the time, and prices are adjusted consistently. The data design follows four conventions:

- **Unified security identifiers** — `<trading_code>.<namespace>`, such as `600000.XSHG`, `000001.XSHE` and `AAPL.US`. The namespace separates equal codes in different markets, and codes resolve at a point in time, so renames and reused codes never land on another security.
- **Point-in-time queries with `as_of`** — rebuild the security universe of a past date and select the financial statements disclosed by then, avoiding look-ahead and survivorship bias.
- **High-quality adjustment factors, `exfactor`** — computed event by event from corporate actions, with unadjusted, forward-adjusted and backward-adjusted prices; `get_ex_factor` returns each event's factor and the cumulative factor, so every adjustment can be traced.
- **One function design for Python and C++** — both clients implement one contract (`contract/contract.json`): function names, parameter order and defaults, validation and errors, returned columns; the same calls are sent through both clients to one server and compared item by item.

## Install

```bash
pip install libfinance
```

From source:

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance/python
pip install -e .
```

> [!TIP]
> **Using C++?** The C++ client matches the Python functions one for one, is added to a project with CMake `FetchContent` and needs Apache Arrow C++. Installing, building and examples: [cpp/readme_en.md](https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/readme_en.md).

## Quick start

Once the service is configured ([installation and connection](https://libfinance.readthedocs.io/en/latest/getting_started/installation.html)), you can query. The outputs below are real runs; the data keeps updating, so row counts and values may differ.

**Security catalog** — both markets in one table, with the same columns:

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

**Sessions** — pass calendar dates, get the sessions among them (`market="us"` for US equities):

```python
from libfinance import get_trading_dates

get_trading_dates("2024-05-11", "2024-05-20")
```

```text
DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
               '2024-05-17', '2024-05-20'],
              dtype='datetime64[us]', freq=None)
```

**Prices** — one call, both markets; US stocks have no price limits, so `limit_up` is `NaN` and the table keeps its structure:

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

`adjust_type="none"` gives the prices actually traded; without it you get forward-adjusted prices (`"pre"`), see [price conventions](https://libfinance.readthedocs.io/en/latest/data/price.html).

**Factors** — the library name `system/alpha158` expands to 158 factors, one column each:

```python
from libfinance import get_factor_exposure

f = get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158", "2026-09-07", "2026-09-10")
f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(4)   # first 6 columns, short names
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

Step by step: [quickstart](https://libfinance.readthedocs.io/en/latest/getting_started/quickstart.html).

## A-shares and US equities share one vocabulary

The unification holds at three layers.

| Layer | What is shared | Example |
| --- | --- | --- |
| Security identifiers | Both are written `<trading_code>.<namespace>`; the granularity of the namespace follows the scope needed to remove ambiguity in that market | `600000.XSHG`, `AAPL.US` |
| Functions and arguments | Both markets go through the same functions with the same argument names; `as_of` and `adjust_type` carry the same meaning | `get_price`, `instruments`, `get_dividends` |
| Result shape | The same columns and the same index; a field that does not apply to a market, or that a deployment does not provide, comes back as `NaN` rather than as a separate table | `turnover`, `limit_up`, `limit_down` for US equities |

Only queries that do not name a security need the market stated: trading calendars, the full security master, and coverage ranges. When you query by security, the namespace already carries the market, and one list may mix the two.

```python
from libfinance import instruments, get_trading_dates

instruments(["000001.XSHE", "AAPL.US"])                      # the namespace carries the market
get_trading_dates("2024-01-01", "2024-01-31", market="us")   # no security named
```

What is shared is the vocabulary and the calling convention; the differences in the data remain. The "Markets" column below shows which markets each kind of data covers, and [Querying US equities](https://libfinance.readthedocs.io/en/latest/howto/us_market.html) goes through it function by function.

## What data is here

| Data | Markets | Main functions | Notes |
| --- | --- | --- | --- |
| Trading calendar | CN · US | `get_trading_dates` | Sessions, ranges, N sessions forward or back |
| Security catalog | CN · US | `all_instruments`, `instruments` | Stocks, indexes, industries, themes; codes, names, listing and delisting dates |
| Daily bars | CN · US | `get_price` | OHLC, volume, turnover, price limits; adjustable |
| Adjustment factors | CN · US | `get_ex_factor` | Event and cumulative factors by ex-date |
| Shares | CN · US | `get_shares` | Per-session total and floating shares |
| Dividends / splits / allotments | CN · US | `get_dividends`, `get_splits`, `get_allotments` | Ex-rights events; allotments are A-share only |
| Spinoffs | US | `get_spinoffs` | A-shares do not produce these events |
| Financial statements (PIT) | CN · US | `get_pit_financials_ex` | By quarter, with restatement history |
| Financial metrics | CN · US | `get_financial_metrics` | Derived financial metrics per trading day |
| Industry classification | CN · US | `get_instrument_industry`, `get_industry_constituents`, `get_industry_weights` | Shenwan, GICS and more |
| Index constituents and weights | CN · US | `get_index_constituents`, `get_index_weights` | CSI, S&P and more |
| Theme constituents and weights | CN | `get_theme_constituents`, `get_theme_weights` | THS themes |
| Daily factors | CN | `get_factor_exposure`, `list_factor_libraries`, `list_factors` | alpha158, qlib, Barra CNE5 / CNE6 |
| Live quotes | CN | `get_last_quotes`, `QuoteApi` | Latest snapshots and streaming subscription |

How far back the history goes and how current it is depend on the service you connect to. **Do not copy the dates from the documentation** — check them yourself with the two functions in [data freshness](https://libfinance.readthedocs.io/en/latest/data/freshness.html).

## Concepts

| Topic | What it solves |
| --- | --- |
| [Unified security identifiers](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html) | Distinguish markets, security identities, and historical codes to join data correctly |
| [Point-in-time queries with as_of](https://libfinance.readthedocs.io/en/latest/concepts/point_in_time.html) | Reconstruct historical universes and visible financial statements to avoid look-ahead and survivorship bias |
| [High-quality adjustment factors, exfactor](https://libfinance.readthedocs.io/en/latest/concepts/exfactor.html) | Understand corporate actions and the calculation and use of three price conventions |
| [One function design for Python and C++](https://libfinance.readthedocs.io/en/latest/concepts/python_cpp.html) | One contract binds both clients: functions, parameters, errors and returned columns match, and are checked item by item |

## Documentation and examples

| | |
| --- | --- |
| [📗 English documentation](https://libfinance.readthedocs.io/en/latest/) | Concepts, data notes, how-to guides, and the API reference |
| [📘 中文文档](https://libfinance.readthedocs.io/zh-cn/latest/) | The same documentation tree in Chinese |
| [💻 Example scripts](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) | Runnable examples by data family, Python and C++ side by side, to read alongside the reference |
| [🧩 How-to guides](https://libfinance.readthedocs.io/en/latest/howto/index.html) | End-to-end recipes: price panels, PIT backtests, live subscriptions |
| [🩺 Troubleshooting](https://libfinance.readthedocs.io/en/latest/howto/troubleshooting.html) | Organized by **symptom**: start from the line that matches what you see |

The API reference groups functions into contracts and calendars, market data, fundamentals, industries, indexes and themes, corporate actions, live quotes, and factors; every function has examples in Python and C++ with their real output.

## Community

Questions and requests are welcome in [Issues](https://github.com/StateOfTheArt-quant/libfinance/issues). Follow us on WeChat for updates:

<div align="center">
    <img alt="WeChat QR code" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="600" height="220">
</div>
