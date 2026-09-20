=========================================
Financial data without look-ahead bias
=========================================

**Goal**: use financial data in a backtest such that every point in time only sees
numbers that were genuinely visible then.

In one line: **pass the current backtest date as ``as_of`` on every query.**

How much difference it makes
============================

Take FY2023 net profit for three stocks, seen from 2024-06-30 and seen today:

.. code-block:: python

    from libfinance import get_pit_financials_ex

    codes = ["000001.XSHE", "000016.XSHE", "600000.XSHG"]

    # What the backtest date could see
    past = get_pit_financials_ex(codes, ["net_profit"], "2023q4", "2023q4",
                                 as_of="2024-06-30")
    # What we can see today (no as_of)
    now = get_pit_financials_ex(codes, ["net_profit"], "2023q4", "2023q4")

.. code-block:: text

    >>> past
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000001.XSHE   2023q4  2024-04-20  4.645500e+10            1
    000016.XSHE   2023q4  2024-04-29 -2.635887e+09            1
    600000.XSHG   2023q4  2024-04-30  3.742900e+10            1

    >>> now
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000001.XSHE   2023q4  2026-03-21  4.645500e+10            1
    000016.XSHE   2023q4  2026-04-29 -2.730376e+09            1
    600000.XSHG   2023q4  2026-03-31  3.742900e+10            1

    >>> now["net_profit"] - past["net_profit"]
    000001.XSHE  2023q4            0.00
    000016.XSHE  2023q4    -94489273.48        <- 94.5m different
    600000.XSHG  2023q4            0.00

One of three names was restated, deepening the loss by 94.5 million. Note the
``info_date``: without ``as_of``, the version you get was published in **2026**.

A real backtest has hundreds or thousands of names across dozens of quarters.
Restatements will not be the exception.

The correct workflow
====================

.. code-block:: python

    from libfinance import (get_trading_dates, get_index_weights,
                            get_pit_financials_ex, get_price)

    for d in get_trading_dates("2024-01-01", "2024-06-30"):
        day = d.strftime("%Y-%m-%d")

        # 1. The universe as of that day
        pool = get_index_weights(index_code="000300.XSHG", date=day)
        codes = list(pool["order_book_id"])

        # 2. The financials visible on that day
        fin = get_pit_financials_ex(codes, ["net_profit"], "2023q1", "2023q4",
                                    as_of=day)

        # 3. Prices (never restated, so no as_of needed)
        px = get_price(codes, day, day)

        ...   # your strategy

Which data needs ``as_of``
==========================

.. list-table::
    :header-rows: 1
    :widths: 36 16 48

    *   - Data
        - Needed?
        - Why
    *   - :func:`~libfinance.get_pit_financials_ex`
        - **Yes**
        - Statements are restated
    *   - :func:`~libfinance.get_factor`
        - **Yes**
        - Derived from statements
    *   - :func:`~libfinance.get_dividends` and other corporate actions
        - **Yes**
        - Events are revised and cancelled
    *   - :func:`~libfinance.get_concept_weights`
        - **Yes**
        - Membership changes
    *   - :func:`~libfinance.get_price`
        - No
        - Prices are final once set
    *   - :func:`~libfinance.get_trading_dates`
        - No
        - The calendar is a fact

:func:`~libfinance.get_index_weights` and
:func:`~libfinance.get_instrument_industry` take ``date`` instead, meaning
"membership/classification on that day" — same effect.

How to confirm you got it right
===============================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    *   - Check
        - Expected
    *   - The ``info_date`` column
        - Every row ``<=`` the ``as_of`` you passed
    *   - Re-run with a later ``as_of``
        - Some numbers change — **that is how you know ``as_of`` is live**
    *   - Backtest returns look implausibly good
        - Suspect look-ahead bias before suspecting the strategy

.. tip::

    The cheapest self-check: run the whole backtest once with ``as_of`` removed.
    If results improve noticeably, your original run really was blocking future
    information. If nothing changes at all, check that ``as_of`` is actually
    reaching the calls.

Inspecting revision history
===========================

To see how often a number changed:

.. code-block:: python

    >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4",
    ...                       statements="all")
      order_book_id quarter  info_date    net_profit  if_adjusted
    0   000016.XSHE  2023q4 2024-04-02 -2.635887e+09            0
    1   000016.XSHE  2023q4 2024-04-29 -2.635887e+09            1
    2   000016.XSHE  2023q4 2024-08-31 -2.635887e+09            1
    3   000016.XSHE  2023q4 2024-10-31 -2.635887e+09            1
    4   000016.XSHE  2023q4 2025-04-15 -2.635887e+09            1
    5   000016.XSHE  2023q4 2026-04-29 -2.730376e+09            1

``if_adjusted`` of ``0`` marks the originally reported figure. More in
:doc:`../data/point_in_time`.
