==========
Quickstart
==========

Four functions, one complete path: **security catalog → sessions → prices → factors**. The catalog
and the calendar are the frame of reference for every other query: a code must resolve to a real
security and a date must be a session, or the later queries come back empty or fail.

.. note::

    Every output below is a real run against the public service. The data keeps updating, so your
    row counts and values may differ; check how current it is with :doc:`../data/freshness` --
    **do not copy the dates**.

Security catalog: all_instruments
=================================

.. code-block:: python

    >>> from libfinance import all_instruments
    >>> stocks = all_instruments(type="stock")
    >>> stocks.groupby("market").size()

.. code-block:: text

    market
    CN    5572
    US    5383
    dtype: int64

.. code-block:: python

    >>> stocks.set_index("order_book_id").loc[
    ...     ["600000.XSHG", "000001.XSHE", "AAPL.US", "NVDA.US"], ["market", "exchange", "name"]]

.. code-block:: text

                  market exchange                               name
    order_book_id
    600000.XSHG       CN     XSHG                               浦发银行
    000001.XSHE       CN     XSHE                               平安银行
    AAPL.US           US     XNAS          Apple Inc. - Common Stock
    NVDA.US           US     XNAS  NVIDIA Corporation - Common Stock

Both markets are in one table with the same columns. ``order_book_id`` is the code and the only
identifier the other functions take; ``name`` is the name. ``type`` also takes ``index``,
``industry`` and ``theme``; pass ``as_of`` for the catalog of a past date.

Sessions: get_trading_dates
===========================

.. code-block:: python

    >>> from libfinance import get_trading_dates
    >>> get_trading_dates("2024-05-11", "2024-05-20")

.. code-block:: text

    DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                   '2024-05-17', '2024-05-20'],
                  dtype='datetime64[us]', freq=None)

You pass calendar dates and get back the sessions among them: 11-12 and 18-19 May are weekends.
Calendars are per market: ``market="cn"`` by default, ``market="us"`` for US equities.

Prices: get_price
=================

.. code-block:: python

    >>> from libfinance import get_price
    >>> get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05",
    ...           fields=["open", "close", "volume", "limit_up"], adjust_type="none")

.. code-block:: text

                                open   close    volume  limit_up
    order_book_id datetime
    600000.XSHG   2024-03-01    7.13    7.11  29431801      7.87
                  2024-03-04    7.12    7.07  27855963      7.82
                  2024-03-05    7.05    7.16  41756232      7.78
    AAPL.US       2024-03-01  179.55  179.66  73563100       NaN
                  2024-03-04  176.15  175.10  81510101       NaN
                  2024-03-05  170.76  170.12  95132400       NaN

One call, both markets, one table indexed by ``(order_book_id, datetime)``. US stocks have no
price limits, so ``limit_up`` is ``NaN`` -- the column stays, and the table's structure does not
depend on the market. Select one security with ``df.loc["AAPL.US"]`` and one day with
``df.xs("2024-03-04", level="datetime")``.

.. important::

    ``adjust_type="none"`` here gives the prices actually traded that day. **Without it you get
    forward-adjusted prices** (``adjust_type="pre"``): history is adjusted for later dividends and
    splits and differs from what traded. The three conventions are explained in :doc:`../data/price`.

Factors: get_factor_exposure
============================

.. code-block:: python

    >>> from libfinance import get_factor_exposure
    >>> f = get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158", "2026-09-07", "2026-09-10")
    >>> f.shape
    (8, 158)
    >>> f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(4)   # first 6 columns, short names

.. code-block:: text

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

The library name ``system/alpha158`` expands to its 158 factors, one column each, named in full
(``system/alpha158/KMID``). For a few factors pass their full names, e.g.
``["system/alpha158/KMID", "system/barra-cne5/SIZE"]``; list libraries and factors with
:func:`~libfinance.list_factor_libraries` and :func:`~libfinance.list_factors`.

Next
====

* :doc:`../howto/price_panel`: a panel of the last N sessions, and where it goes wrong
* :doc:`../concepts/point_in_time`: why a backtest passes ``as_of``
* :doc:`../data/index`: what each kind of data means and covers
* :doc:`../reference/factors`: the factor functions and examples
