================
Trading calendar
================

The calendar is the frame of reference for every date-based query: only once you
know which days are sessions can you tell whether "no data for that day" means a
suspension or simply no trading.

.. code-block:: python

    >>> from libfinance import get_trading_dates
    >>> get_trading_dates("2024-05-11", "2024-05-20")
    DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                   '2024-05-17', '2024-05-20'],
                  dtype='datetime64[ns]', freq=None)

You pass calendar dates for the range endpoints; you get back only sessions.
11–12 May is a weekend, as is 18–19 May.

Common operations
=================

.. list-table::
    :header-rows: 1
    :widths: 46 54

    *   - What you want
        - Function
    *   - Sessions in a range
        - :func:`~libfinance.get_trading_dates`
    *   - Is this day a session?
        - :func:`~libfinance.is_trading_date`
    *   - N sessions back
        - :func:`~libfinance.get_previous_trading_date`
    *   - N sessions forward
        - :func:`~libfinance.get_next_trading_date`
    *   - Last N sessions up to and including a day
        - :func:`~libfinance.get_n_trading_dates_until`
    *   - How many sessions in a range
        - :func:`~libfinance.count_trading_dates`
    *   - Every session
        - :func:`~libfinance.get_all_trading_dates`

.. code-block:: python

    >>> from libfinance import (get_previous_trading_date, is_trading_date,
    ...                         count_trading_dates, get_n_trading_dates_until)
    >>> get_previous_trading_date("2020-05-18", n=3)
    Timestamp('2020-05-13 00:00:00')
    >>> is_trading_date("2024-05-01")           # Labour Day
    False
    >>> count_trading_dates("2024-01-01", "2024-12-31")
    242
    >>> get_n_trading_dates_until("2024-03-11", 5)
    DatetimeIndex(['2024-03-05', '2024-03-06', '2024-03-07', '2024-03-08',
                   '2024-03-11'], dtype='datetime64[ns]', freq=None)

US market
=========

Same functions, plus ``market="us"``:

.. code-block:: python

    >>> get_trading_dates("2024-01-01", "2024-01-10", market="us")

Omitting ``market`` means A-shares.

How far the calendar reaches
============================

The calendar is not unbounded. It has an explicit **confirmed range**:

.. code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

``confirmed_through`` is how far the publisher has confirmed. Exchanges announce
next year's holidays in advance, so this date is usually in the **future** — the
service above is confirmed to year end.

Querying outside the range raises:

.. code-block:: python

    >>> get_trading_dates("2027-01-01", "2027-01-10")
    CalendarCoverageError: cn 的查询 2027-01-01 超出 release 确认范围
                           1990-12-19..2026-12-31

.. admonition:: Why raise instead of returning nothing
    :class: important

    Because **"nobody has published that day" and "that day is not a session" are
    different statements.**

    If this returned an empty result, your code would carry on with a few days
    missing and nothing to indicate it. In a backtest that kind of silent gap is
    very hard to spot. Raising forces you to handle it.

    For the same reason, stepping N sessions forward or back past the edge of the
    range raises rather than returning the endpoint. Returning the endpoint would
    be a **wrong answer**: you asked for "the third session back" and got "the
    earliest session", and the two are indistinguishable.

.. warning::

    **A confirmed calendar date is not a date with prices.** The calendar reaches
    2026-12-31; prices only reach the last closed session. These are two different
    upper bounds, and confusing them is the most common source of errors — see
    :doc:`freshness`.
