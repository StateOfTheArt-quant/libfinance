<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo_dark.svg">
  <img alt="libfinance" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/libfinance_logo.svg" width="300">
</picture>

**A Python financial data client for quantitative research and backtesting, with one calling convention for A-shares and US equities**

[![PyPI](https://img.shields.io/pypi/v/libfinance?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/libfinance/)
[![docs en](https://img.shields.io/readthedocs/libfinance-en?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20en)](https://libfinance.readthedocs.io/en/latest/)
[![docs zh-cn](https://img.shields.io/readthedocs/libfinance?style=flat-square&logo=readthedocs&logoColor=white&label=docs%20zh-cn)](https://libfinance.readthedocs.io/zh-cn/latest/)

[Documentation](https://libfinance.readthedocs.io/en/latest/) ·
[中文](https://github.com/StateOfTheArt-quant/libfinance/blob/main/README.md) ·
[Examples](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example) ·
[Citation](#citation)

</div>

---

## Overview

`libfinance` is a lightweight Python client. The data lives on a server; the client sends queries and returns the results as pandas `DataFrame` or `Series` objects. It covers trading calendars, security master data, daily prices, adjustment factors, corporate actions, financial statements, industry, index and concept constituents, and live quote subscriptions for A-shares.

A-shares and US equities go through the same functions, with the same argument names and the same result structure. The two markets differ in the data itself (US equities have no daily price limits, for example), not in how you query it.

## Design

In historical research, the most common errors come less from wrong prices than from misaligned objects, observation dates, or price conventions. The library handles three of these at the data level.

**Security identity.** On its own, `000001` can mean either the SSE Composite Index or Ping An Bank. Securities are written as `<trading_code>.<namespace>` (called `order_book_id` in the API), for example `000001.XSHG`, `000001.XSHE`, and `AAPL.US`. Codes also have validity periods: after a rename or code reuse, the same code can refer to different companies in different years, so `instruments` accepts `as_of` to resolve a code at a historical date.
→ [Unified security identifiers](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html)

**Observation date, `as_of`.** A report's fiscal period and its disclosure date are different things, and reports can be restated after disclosure. For example, the 2023 annual net profit of `000016.XSHE` has 6 versions in the database; the last one was published in April 2026 and revised the loss from 2.636 to 2.730 billion CNY. A 2024 backtest that uses this figure is using information that did not exist yet. `as_of` makes the observation date explicit: financial queries return only versions disclosed by that date, and security universes are rebuilt from the listing status at that date, putting later-delisted securities back into history to avoid survivorship bias.
→ [Point-in-time queries with as_of](https://libfinance.readthedocs.io/en/latest/concepts/point_in_time.html)

**Price convention.** Cash dividends, stock dividends, and rights issues cause mechanical price jumps that are not investment gains or losses. Adjustment factors follow the `PRIOR_CLOSE` convention: an event factor is the prior close divided by the theoretical ex-price, and the cumulative factor is the product of all event factors up to the ex-date. Prices can be returned unadjusted, forward-adjusted, or backward-adjusted, and every event and cumulative factor can be inspected with `get_ex_factor`. Note that this convention is the reciprocal of a "multiplier applied to historical prices"; check the direction before comparing with other data sources.
→ [Adjustment factors, exfactor](https://libfinance.readthedocs.io/en/latest/concepts/exfactor.html)

## Installation and connection

Requires Python 3.7 or later.

```bash
pip install libfinance
```

Or from source:

```bash
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance
pip install -e .
```

`import libfinance` does not open a connection; the client connects on the first query. The default endpoint is `libfinance.tech:8080`. To connect to another service (a local deployment, for example), use either of the following:

```bash
# Option 1: environment variables, set before importing libfinance
export LIBFINANCE_HOST=127.0.0.1
export LIBFINANCE_PORT=8080
```

```python
# Option 2: initialize explicitly before the first query
from libfinance import init_client
init_client(host="127.0.0.1", port=8080)
```

## Minimal example

```python
from libfinance import instruments, get_price, get_ex_factor

# Resolve security information at a historical date
print(instruments("600000.XSHG", as_of="2024-03-01"))

# Request unadjusted prices explicitly to get actual traded prices
print(get_price(
    ["000001.XSHE", "600000.XSHG"],
    "2024-03-01", "2024-03-06", adjust_type="none",
))

# Inspect event and cumulative adjustment factors for each ex-date
print(get_ex_factor("600000.XSHG", "2023-01-01", "2024-12-31"))
```

`get_price` returns a `DataFrame` indexed by `(order_book_id, datetime)`. Select one security with `df.loc["000001.XSHE"]` and one date with `df.xs("2024-03-04", level="datetime")`. The [quickstart](https://libfinance.readthedocs.io/en/latest/getting_started/quickstart.html) explains the output line by line.

## Defaults to know before you start

These are not advanced topics; they are default behavior. Without knowing them, your code still runs, but the numbers may be wrong.

1. **Without `adjust_type`, `get_price` returns forward-adjusted prices.** For `000001.XSHE` on 2024-03-01, the forward-adjusted close is 8.81, while the actual traded price was 10.49. Pass `adjust_type="none"` for actual traded prices. The default changed from `"none"` to `"pre"` in 0.0.6; code that relied on the old behavior must set it explicitly. See the [changelog](https://libfinance.readthedocs.io/en/latest/about/changelog.html).
2. **Prices extend only to the last closed and ingested trading day.** The trading calendar is published through year-end; prices are not. An `end_date` beyond price coverage produces a warning and then an error, rather than a silently shorter table. Check the boundaries with `get_price_coverage()` and `get_calendar_coverage()` instead of copying dates from the documentation.
3. **Pass `as_of` when querying financials in a backtest.** Without it, you get the latest restated version as of today.

## Data coverage

| Data | Markets | Main functions | Notes |
| --- | --- | --- | --- |
| Trading calendar | CN · US | `get_trading_dates` | Sessions, ranges, N sessions forward or back |
| Security master | CN · US | `all_instruments`, `instruments` | Code, name, type, listing and delisting dates |
| Daily prices | CN · US | `get_price` | OHLC, volume, turnover; adjustable |
| Adjustment factors | CN · US | `get_ex_factor` | Event and cumulative factors by ex-date |
| Share capital | CN | `get_shares` | Total and floating shares per session |
| Dividends / splits / allotments | CN · US | `get_dividends`, `get_splits`, `get_allotments` | Ex-rights events, the source of price gaps |
| Spinoffs | US | `get_spinoffs` | Not applicable to A-shares |
| Financial statements (PIT) | CN | `get_pit_financials_ex` | By quarter, with restatement history |
| Financial factors | CN | `get_factor` | Factors derived from quarterly financials |
| Industry classification | CN | `get_industry_mapping` | Shenwan three-level taxonomy |
| Index constituents and weights | CN | `get_index_weights` | Constituents and weights on any session |
| Concept board constituents | CN | `get_concept_weights` | THS concept taxonomy |
| Live quotes | CN | `QuoteApi` | Subscription push |

When you query by security, the namespace in the code determines the market, and one list may mix both markets. Only queries that do not name a security (trading calendars, the full security master, coverage ranges) take an explicit `market`. Fields that do not apply to a market, or that a deployment does not provide, come back as `NaN`; the table structure stays the same.

```python
from libfinance import instruments, get_trading_dates

instruments(["000001.XSHE", "AAPL.US"])                      # the namespace carries the market
get_trading_dates("2024-01-01", "2024-01-31", market="us")   # no security named
```

## Scope and limitations

- Prices are daily only (`frequency="1d"`); minute bars and tick data are not provided.
- Share capital, financials, industry, index constituents, concept constituents, and live quotes cover A-shares only. US equities have no price-limit fields, and some deployments do not provide US turnover. See [Querying US equities](https://libfinance.readthedocs.io/en/latest/howto/us_market.html) for each function.
- Date coverage depends on the service you connect to; dates in the documentation are illustrative.
- The project is at 0.x and the API may still change (for example, `index_id` in `get_index_weights` was renamed to `index_code`). Every change that alters the behavior of existing code is recorded in the [changelog](https://libfinance.readthedocs.io/en/latest/about/changelog.html).

## Documentation

- [Quickstart](https://libfinance.readthedocs.io/en/latest/getting_started/quickstart.html): trading dates, securities, prices — one complete query path
- [Concepts](https://libfinance.readthedocs.io/en/latest/concepts/security_identifiers.html): security identifiers, point-in-time, adjustment factors
- [Data notes](https://libfinance.readthedocs.io/en/latest/data/index.html): conventions and freshness for each kind of data
- [How-to guides](https://libfinance.readthedocs.io/en/latest/howto/index.html): price panels, PIT backtests, returns, live subscriptions
- [API reference](https://libfinance.readthedocs.io/en/latest/reference/contracts.html): parameters, with examples and printed output
- [Troubleshooting](https://libfinance.readthedocs.io/en/latest/howto/troubleshooting.html): organized by the symptom you see
- [Example scripts](https://github.com/StateOfTheArt-quant/libfinance/tree/main/example): runnable scripts matching the six API reference groups

Chinese documentation: <https://libfinance.readthedocs.io/zh-cn/latest/>

## Citation

If `libfinance` helps your research, you can cite it as:

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

## Maintenance and feedback

The project is maintained by StateOfTheArt.Quant; the core contributor is Yu Jiang ([@walkacross](https://github.com/walkacross)). Please open an [Issue](https://github.com/StateOfTheArt-quant/libfinance/issues) for data-convention questions, bugs, or feature requests. Including the calling code and the actual output helps us locate the problem faster.

Project updates are also posted on our WeChat account:

<div align="center">
    <img alt="WeChat QR code" src="https://raw.githubusercontent.com/StateOfTheArt-quant/libfinance/main/docs/_shared/_static/img/code.png" width="300">
</div>
