# libfinance

\[ English | [中文](README_zh.md) \]

`libfinance` gives quantitative researchers historical data for Chinese A-share
and US equity markets: prices, security master data, trading calendars, corporate
actions, financials, share capital, industry classification, index and concept
constituents, plus live market data subscription.

## Install

```bash
$ pip install libfinance
```

Or from source:

```bash
$ git clone https://github.com/StateOfTheArt-quant/libfinance.git
$ cd libfinance
$ pip install -e .
```

## Quick start

```python
from libfinance import get_trading_dates, get_price

trading_dates = get_trading_dates(start_date="2024-05-11", end_date="2024-05-20")
print(trading_dates)

data = get_price(["000001.XSHE", "600000.XSHG"], "2024-03-01", "2024-03-06")
print(data)
```

```text
DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
               '2024-05-17', '2024-05-20'],
              dtype='datetime64[ns]', freq=None)

                          open      high       low     close        volume      turnover
order_book_id datetime
000001.XSHE   2024-03-01  8.897049  8.905450  8.762627  8.813035  2.175959e+08  1.917689e+09
              2024-03-04  8.779430  8.821436  8.670212  8.678613  1.971024e+08  1.719563e+09
              2024-03-05  8.653409  8.796232  8.619804  8.762627  2.163123e+08  1.889144e+09
              2024-03-06  8.737423  8.779430  8.678613  8.678613  1.601692e+08  1.396940e+09
600000.XSHG   2024-03-01  6.373316  6.400132  6.346500  6.355438  3.292615e+07  2.094740e+08
              2024-03-04  6.364377  6.364377  6.301806  6.319683  3.116322e+07  1.971570e+08
              2024-03-05  6.301806  6.418009  6.292867  6.400132  4.671382e+07  2.976761e+08
              2024-03-06  6.409071  6.453764  6.364377  6.364377  2.899600e+07  1.858478e+08
```

> **Those are not the prices that traded.** `adjust_type` defaults to `"pre"`
> (forward-adjusted). On 2024-03-01, `000001.XSHE` actually traded at 10.49, not
> 8.81. Pass `adjust_type="none"` for traded prices — see
> [Prices and adjustment](https://libfinance.readthedocs.io/en/latest/data/price.html).

## Documentation

- [English](https://libfinance.readthedocs.io/en/latest/)
- [中文](https://libfinance.readthedocs.io/zh-cn/latest/)

Worth reading before you rely on the numbers:

| Topic | Why |
| --- | --- |
| [Prices and adjustment](https://libfinance.readthedocs.io/en/latest/data/price.html) | The default is forward-adjusted; volume is adjusted too, turnover is not |
| [How recent the data is](https://libfinance.readthedocs.io/en/latest/data/freshness.html) | `end_date` cannot be today |
| [Restatements and `as_of`](https://libfinance.readthedocs.io/en/latest/data/point_in_time.html) | Financial statements get restated; backtests need `as_of` |

## Examples

Runnable scripts live in [`example/`](example/).

## Community

Follow us on WeChat for updates:

<div>
    <img alt="qr" src="/docs/_shared/_static/img/code.png" width="600" height="220">
</div>
