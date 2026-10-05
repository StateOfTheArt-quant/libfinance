=========================
How recent the data is
=========================

This chapter answers one concrete question: **why does "give me the last 10
sessions" fail?**

The symptom:

.. code-block:: python

    >>> import datetime
    >>> today = datetime.date.today().isoformat()      # '2026-09-19'
    >>> get_price(["600000.XSHG"], "2026-09-01", today)
    UserWarning: get_price: end_date=2026-09-19 超出行情覆盖（最新已收盘交易日
                 2026-09-18）...
    RpcError: XSHG query 2026-09-01..2026-09-19 is outside coverage
              2000-01-04..2026-09-18; a date this release does not reach is not
              a date with no trading

Three different upper bounds
============================

"The last 10 days" fails because it assumes something untrue: **that today has
data**. In fact there are at least three distinct upper bounds here.

.. list-table::
    :header-rows: 1
    :widths: 24 20 56

    *   - Bound
        - Typically
        - What it is
    *   - Calendar confirmed through
        - **the future** (year end)
        - Exchange holiday schedules are published in advance, so the calendar
          reaches into next year
    *   - Price coverage
        - yesterday / the day before
        - The last session that has **closed and been ingested**
    *   - Adjustment factors
        - possibly earlier still
        - Factors require corporate actions to be finalised first

Which yields the counter-intuitive conclusion:

.. admonition:: A day on the calendar is not a day with prices
    :class: important

    The calendar says 2026-12-31 is confirmed; prices stop at 2026-09-18. They
    answer different questions: the calendar says whether the market is open, the
    price data says whether that day's numbers have arrived.

    That is exactly what the server says when it refuses an out-of-range query —
    *a date this release does not reach is not a date with no trading*. It refuses
    to let "the data hasn't arrived" masquerade as "there was no trading", because
    the latter would quietly cost you days without you noticing.

Asking for the bound
====================

.. code-block:: python

    >>> from libfinance import get_price_coverage
    >>> get_price_coverage()
    {'XSHE': {'start': '2000-01-04', 'end': '2026-09-18',
              'raw_end': '2026-09-18', 'adjust_cutoff': '2026-09-18'},
     'XSHG': {'start': '2000-01-04', 'end': '2026-09-18',
              'raw_end': '2026-09-18', 'adjust_cutoff': '2026-09-18'}}

.. list-table::
    :header-rows: 1
    :widths: 22 78

    *   - Key
        - Meaning
    *   - ``start``
        - Earliest date with prices
    *   - ``end``
        - Last date available for **adjusted** prices. Since ``adjust_type``
          defaults to ``"pre"``, which needs factors, this is already the minimum
          of ``raw_end`` and ``adjust_cutoff`` — **using it as ``end_date`` is
          safe**
    *   - ``raw_end``
        - Last date available for unadjusted prices
    *   - ``adjust_cutoff``
        - How far adjustment factors have been computed

For US equities pass ``market="us"``:

.. code-block:: python

    >>> get_price_coverage(market="us")
    {'US': {'start': None, 'end': '2026-08-21',
            'raw_end': None, 'adjust_cutoff': '2026-08-21'}}

US upstream data is partitioned by month, so there is no day-level bound — and
this function will **not** invent one from a month. The bound for adjusted prices
comes from the adjustment cutoff, which is day-level and authoritative.

The calendar bound is separate
==============================

:func:`~libfinance.get_calendar_coverage` answers the calendar question:

.. code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

The other end can be clamped too
================================

Everything above concerns the **right-hand** end of the range. The left end may
be limited as well: the server may only allow querying the last two years or so,
and an earlier ``start_date`` is silently pulled forward to that boundary.

The awkward part is that if ``end_date`` is also earlier than the boundary, it is
**pulled forward with it** — start and end collide and you get an empty table.
And an empty table cannot tell you whether the period has no data or the range was
clamped.

So the client warns before a request gets clamped, naming the boundary date. The
warning takes this shape (client warnings are emitted in Chinese):

.. code-block:: text

    UserWarning: get_price: 可查区间的起点是 <boundary>，比它更早的
                 start_date=<yours> 会被服务端夹到边界（end_date 早于边界时也会
                 一起上拉，结果可能是空表）。

Move ``start_date`` inside that boundary when you see it. No warning means your
range was not clamped.

.. note::

    Not every deployment applies this limit. When the server declares no range
    restriction, this warning never appears and history is not clamped.

The correct pattern
===================

To express "the last N sessions", ask for the bound first, then count back in
**sessions** — not in calendar days from today:

.. code-block:: python

    from libfinance import get_price, get_price_coverage, get_n_trading_dates_until

    end = min(v["end"] for v in get_price_coverage().values())
    sessions = get_n_trading_dates_until(end, 10)

    df = get_price(["600000.XSHG"],
                   sessions[0].strftime("%Y-%m-%d"),
                   sessions[-1].strftime("%Y-%m-%d"))

Two details:

* ``min(...)`` because exchanges may differ in coverage — take the conservative one;
* :func:`~libfinance.get_n_trading_dates_until` rather than ``end - 10 days``,
  because weekends and holidays are not sessions.

A complete runnable version is in :doc:`../howto/price_panel`.

.. tip::

    **Transferable rule**: whenever you write "today" or ``datetime.now()`` as the
    right-hand endpoint of a data query, stop and ask whether that data set is
    current through today. For most historical data sets the answer is no.
