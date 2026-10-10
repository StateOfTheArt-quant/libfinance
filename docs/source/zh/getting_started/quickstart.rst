========
快速开始
========

四个函数走通一条完整链路：\ **证券目录 → 交易日 → 行情 → 因子**\ 。证券目录和交易日历是其余查询的参照系：
代码要能解析成一只真实的证券，日期要落在交易日上，否则后面的查询会返回空表或报错。

..  note::

    下面的输出都是对公开服务的真实运行结果。数据会持续更新，你看到的行数与数值可能不同；
    能查到哪一天，用 :doc:`../data/freshness` 里的函数确认，\ **不要照抄日期**\ 。

证券目录：all_instruments
=========================

..  code-block:: python

    >>> from libfinance import all_instruments
    >>> stocks = all_instruments(type="stock")
    >>> stocks.groupby("market").size()

..  code-block:: text

    market
    CN    5572
    US    5383
    dtype: int64

..  code-block:: python

    >>> stocks.set_index("order_book_id").loc[
    ...     ["600000.XSHG", "000001.XSHE", "AAPL.US", "NVDA.US"], ["market", "exchange", "name"]]

..  code-block:: text

                  market exchange                               name
    order_book_id
    600000.XSHG       CN     XSHG                               浦发银行
    000001.XSHE       CN     XSHE                               平安银行
    AAPL.US           US     XNAS          Apple Inc. - Common Stock
    NVDA.US           US     XNAS  NVIDIA Corporation - Common Stock

两个市场在同一张表里，列相同。\ ``order_book_id`` 是代码，也是其余函数认的唯一标识；\ ``name`` 是名称。
``type`` 还可以取 ``index``\ 、\ ``industry``\ 、\ ``theme``\ ；传 ``as_of`` 得到某个历史日期的目录。

交易日：get_trading_dates
=========================

..  code-block:: python

    >>> from libfinance import get_trading_dates
    >>> get_trading_dates("2024-05-11", "2024-05-20")

..  code-block:: text

    DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                   '2024-05-17', '2024-05-20'],
                  dtype='datetime64[us]', freq=None)

区间按自然日给，返回其中的交易日：5 月 11、12 日与 18、19 日是周末，不在结果里。
交易日历按市场区分，默认 ``market="cn"``\ ，美股传 ``market="us"``\ 。

行情：get_price
===============

..  code-block:: python

    >>> from libfinance import get_price
    >>> get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05",
    ...           fields=["open", "close", "volume", "limit_up"], adjust_type="none")

..  code-block:: text

                                open   close    volume  limit_up
    order_book_id datetime
    600000.XSHG   2024-03-01    7.13    7.11  29431801      7.87
                  2024-03-04    7.12    7.07  27855963      7.82
                  2024-03-05    7.05    7.16  41756232      7.78
    AAPL.US       2024-03-01  179.55  179.66  73563100       NaN
                  2024-03-04  176.15  175.10  81510101       NaN
                  2024-03-05  170.76  170.12  95132400       NaN

一次调用混查两个市场，返回一张表，索引是 ``(order_book_id, datetime)``\ 。美股没有涨跌停，
``limit_up`` 为 ``NaN``\ ——列照样在，表结构不因市场而变。取单只证券用 ``df.loc["AAPL.US"]``\ ，
取某一天用 ``df.xs("2024-03-04", level="datetime")``\ 。

..  important::

    这里显式写了 ``adjust_type="none"``\ ，得到当天真实的成交价。\ **不传时默认前复权**
    （\ ``adjust_type="pre"``\ ），历史价格会按之后的分红送转调整，与当天的成交价不同。
    三种口径的区别见 :doc:`../data/price`\ 。

因子：get_factor_exposure
=========================

..  code-block:: python

    >>> from libfinance import get_factor_exposure
    >>> f = get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158", "2026-09-07", "2026-09-10")
    >>> f.shape
    (8, 158)
    >>> f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(4)   # 前 6 列，列名只留因子名

..  code-block:: text

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

传库名 ``system/alpha158`` 展开为它的 158 个因子，每个因子一列，列名是全名
（\ ``system/alpha158/KMID``\ ）。只要几个因子时传全名列表，如
``["system/alpha158/KMID", "system/barra-cne5/SIZE"]``\ ；有哪些库和因子，用
:func:`~libfinance.list_factor_libraries` 与 :func:`~libfinance.list_factors` 查。

接下来
======

* :doc:`../howto/price_panel`\ ：取最近 N 个交易日的行情面板，以及其中容易出错的地方
* :doc:`../concepts/point_in_time`\ ：回测为什么要带 ``as_of``
* :doc:`../data/index`\ ：每一类数据的口径与覆盖范围
* :doc:`../reference/factors`\ ：因子接口与示例
