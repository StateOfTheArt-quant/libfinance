# 示例

按数据族组织、按阅读顺序编号。先读前四个——交易日历、证券目录、日线、复权因子是其余一切的基础：
几乎所有查询都要先确定**哪些日子**、**哪些证券**，再取**价格**，而价格的复权靠**复权因子**。

| # | 数据族 | Python | C++ | 函数 |
| --- | --- | --- | --- | --- |
| 01 | 交易日历 | [01_calendar.py](python/01_calendar.py) | [01_calendar.cpp](cpp/01_calendar.cpp) | `get_trading_dates`、`get_previous_trading_date`、`get_calendar_coverage`… |
| 02 | 证券目录 | [02_instrument.py](python/02_instrument.py) | [02_instrument.cpp](cpp/02_instrument.cpp) | `all_instruments`、`instruments`：股票、指数、行业、主题分类型展示 |
| 03 | 日线 | [03_daybar.py](python/03_daybar.py) | [03_daybar.cpp](cpp/03_daybar.cpp) | `get_price`、`get_price_coverage` |
| 04 | 复权因子 | [04_exfactor.py](python/04_exfactor.py) | [04_exfactor.cpp](cpp/04_exfactor.cpp) | `get_ex_factor` |
| 05 | 公司行为 | [05_corporate_actions.py](python/05_corporate_actions.py) | [05_corporate_actions.cpp](cpp/05_corporate_actions.cpp) | `get_dividends`、`get_splits`、`get_allotments`、`get_spinoffs` |
| 06 | 股本 | [06_shares.py](python/06_shares.py) | [06_shares.cpp](cpp/06_shares.cpp) | `get_shares` |
| 07 | 财务 | [07_financials.py](python/07_financials.py) | [07_financials.cpp](cpp/07_financials.cpp) | `get_pit_financials_ex`、`get_financial_metrics` |
| 08 | 行业 | [08_industry.py](python/08_industry.py) | [08_industry.cpp](cpp/08_industry.cpp) | `get_instrument_industry`、`get_industry_constituents`、`get_industry_weights` |
| 09 | 指数 | [09_index.py](python/09_index.py) | [09_index.cpp](cpp/09_index.cpp) | `get_instrument_indices`、`get_index_constituents`、`get_index_weights` |
| 10 | 主题 | [10_theme.py](python/10_theme.py) | [10_theme.cpp](cpp/10_theme.cpp) | `get_instrument_themes`、`get_theme_constituents`、`get_theme_weights` |
| 11 | 实时快照 | [11_live_quote.py](python/11_live_quote.py) | [11_live_quote.cpp](cpp/11_live_quote.cpp) | `get_last_quotes` |
| 12 | 实时订阅 | [12_live_subscription.py](python/12_live_subscription.py) | [12_live_subscription.cpp](cpp/12_live_subscription.cpp) | `QuoteApi` / `QuoteSpi`：按 order_book_id 订阅 |

`python/tools/fullmarket_health_check.py` 是运维用的全市场行情体检，不是教程。

同一编号的两个文件逐段对应：段落以 `[函数名]` / `[/函数名]` 标记（文档的 `literalinclude` 引用 Python 的这些片段），
改一边时同步另一边。市场由代码本身确定（`600000.XSHG`、`AAPL.US`），中美混查不需要 `market` 参数。

运行前应已配置服务连接（`LIBFINANCE_HOST` / `LIBFINANCE_PORT`）；历史日期需落在服务的数据覆盖内。

```bash
python example/python/03_daybar.py

cmake -S cpp -B cpp/build -DBUILD_EXAMPLES=ON … && cmake --build cpp/build -j
cpp/build/example/libfinance_03_daybar
```
