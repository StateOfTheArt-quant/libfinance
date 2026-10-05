=============================
Fetching the last N sessions
=============================

**Goal**: get a price panel for the last 10 sessions across several stocks.

It sounds like one line, but the intuitive version fails. This guide gives the
correct form and explains why it is correct.

Why the intuitive version fails
===============================

.. code-block:: python

    # Don't do this
    import datetime
    end = datetime.date.today().isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    df = get_price(["600000.XSHG"], start, end)

Two mistakes:

1. **``end`` is today.** Prices only reach the last closed session; today's data
   does not exist yet. The server rejects the whole range — it does not return
   fewer days, it raises.
2. **Ten calendar days is not ten sessions.** Weekends and holidays fall inside,
   so you would actually get six or seven.

The correct form
================

.. code-block:: python

    from libfinance import get_price, get_price_coverage, get_n_trading_dates_until

    # 1. Ask how recent the price data is (exchanges may differ; be conservative)
    end = min(v["end"] for v in get_price_coverage().values())

    # 2. Count back 10 sessions from there
    sessions = get_n_trading_dates_until(end, 10)

    # 3. Use the session endpoints as the range
    df = get_price(["000001.XSHE", "600000.XSHG"],
                   sessions[0].strftime("%Y-%m-%d"),
                   sessions[-1].strftime("%Y-%m-%d"))

A real run:

.. code-block:: text

    >>> end
    '2026-09-18'
    >>> sessions[0].date(), sessions[-1].date(), len(sessions)
    (datetime.date(2026, 9, 7), datetime.date(2026, 9, 18), 10)
    >>> df.shape
    (20, 8)

What each step does
===================

.. list-table::
    :header-rows: 1
    :widths: 30 70

    *   - Step
        - Why it is needed
    *   - ``get_price_coverage()``
        - Asks for the real upper bound. Its ``end`` already accounts for the
          adjustment cutoff, so it is safe to use directly as ``end_date``
    *   - ``min(...)``
        - Exchanges may differ; the minimum guarantees data on both
    *   - ``get_n_trading_dates_until``
        - Counts back in sessions, skipping weekends and holidays

Checking the result
===================

.. list-table::
    :header-rows: 1
    :widths: 36 64

    *   - Check
        - Expected
    *   - ``len(sessions)``
        - Exactly the N you asked for
    *   - ``df.index.get_level_values("datetime").nunique()``
        - Equals N (unless a name was suspended and ``skip_suspended`` is on)
    *   - ``df.index.get_level_values("order_book_id").nunique()``
        - Equals the number of codes you passed; fewer means some did not
          resolve — check the warnings

Handling suspensions
====================

By default suspended days are kept (with zero volume), so every name shares one
date axis, which suits panel alignment. To drop them:

.. code-block:: python

    df = get_price(ids, start, end, skip_suspended=True)

Row counts then differ per name, so ``unstack`` to align before any matrix maths.

If you want traded prices
=========================

The above returns **forward-adjusted** prices. For the prices as they traded:

.. code-block:: python

    df = get_price(ids, start, end, adjust_type="none")

How much they differ, and which to use when, is in :doc:`../data/price`.
