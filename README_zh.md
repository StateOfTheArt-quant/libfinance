# libfinance

\[ [English](README.md) | 中文 \]

`libfinance` 为量化研究者提供 A 股与美股的历史数据：行情、证券主数据、交易日历、
公司行动、财务、股本、行业分类、指数与概念成分，以及实时行情订阅。

## 安装

```bash
$ pip install libfinance
```

或从源码安装：

```bash
$ git clone https://github.com/StateOfTheArt-quant/libfinance.git
$ cd libfinance
$ pip install -e .
```

## 快速开始

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

> **上面这些不是当时的成交价。** `adjust_type` 默认是 `"pre"`（前复权）。
> `000001.XSHE` 在 2024-03-01 的实际成交价是 10.49，不是 8.81。要真实成交价请传
> `adjust_type="none"`——见
> [行情与复权](https://libfinance.readthedocs.io/zh-cn/latest/data/price.html)。

## 文档

- [中文](https://libfinance.readthedocs.io/zh-cn/latest/)
- [English](https://libfinance.readthedocs.io/en/latest/)

在依赖这些数字之前，建议先读三篇：

| 主题 | 为什么 |
| --- | --- |
| [行情与复权](https://libfinance.readthedocs.io/zh-cn/latest/data/price.html) | 默认是前复权；成交量也被复权，成交额不被 |
| [数据更新到哪一天](https://libfinance.readthedocs.io/zh-cn/latest/data/freshness.html) | `end_date` 不能写今天 |
| [财报修订与 as_of](https://libfinance.readthedocs.io/zh-cn/latest/data/point_in_time.html) | 财报会被追溯修订，回测必须传 `as_of` |

## 示例

可直接运行的脚本在 [`example/`](example/)。

## 社区

关注公众号获取更新：

<div>
    <img alt="qr" src="/docs/_shared/_static/img/code.png" width="600" height="220">
</div>
