================
Trading calendar
================

.. currentmodule:: libfinance

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_trading_dates`
      - List trading dates in a range
    * - :func:`~libfinance.is_trading_date`
      - Check whether a date is a trading day
    * - :func:`~libfinance.get_previous_trading_date`
      - Move backward by trading days
    * - :func:`~libfinance.get_next_trading_date`
      - Move forward by trading days
    * - :func:`~libfinance.get_n_trading_dates_until`
      - Build a trailing trading-day window
    * - :func:`~libfinance.count_trading_dates`
      - Count trading days
    * - :func:`~libfinance.get_all_trading_dates`
      - Read the full trading calendar
    * - :func:`~libfinance.get_calendar_coverage`
      - Check the confirmed calendar bounds

Semantics are covered in :doc:`../data/calendar`. Every function takes ``market``,
defaulting to ``"cn"``.

.. py:function:: get_trading_dates(start_date, end_date, market='cn')

    Sessions within a range.

    :param start_date: Start date (calendar date)
    :param end_date: End date (calendar date)
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex`` of sessions
    :raises CalendarCoverageError: if either endpoint falls outside the confirmed range

    **Examples**

    .. lf-examples:: get_trading_dates

    Reading the result: The same range can contain different trading dates in different markets; January 15 illustrates the difference here.

.. py:function:: is_trading_date(date, market='cn')

    Whether a given day is a session.

    :param date: The day to test
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``bool``

    **Examples**

    .. lf-examples:: is_trading_date

    Reading the result: The boolean result can be used directly in a condition.

.. py:function:: get_previous_trading_date(date, n=1, market='cn')

    The n-th session before a given day.

    :param date: Reference day
    :param n: How many sessions back
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping back goes past the start of the range

    **Examples**

    .. lf-examples:: get_previous_trading_date

    Reading the result: Both offsets exclude the input date. n counts trading days, not calendar days.

.. py:function:: get_next_trading_date(date, n=1, market='cn')

    The n-th session after a given day.

    :param date: Reference day
    :param n: How many sessions forward
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping forward goes past the confirmed end

    **Examples**

    .. lf-examples:: get_next_trading_date

    Reading the result: The first trading day after Friday is Monday; n=3 moves to the third trading day.

.. py:function:: get_n_trading_dates_until(date, n, market='cn')

    The last n sessions up to and including a given day.

    :param date: Last day (inclusive)
    :param n: How many sessions
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

    **Examples**

    .. lf-examples:: get_n_trading_dates_until

    Reading the result: A trading-day cutoff includes that day. A Sunday cutoff ends at the preceding Friday.

.. py:function:: count_trading_dates(start_date, end_date, market='cn')

    How many sessions fall in a range.

    :param start_date: Start date
    :param end_date: End date
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``int``

    **Examples**

    .. lf-examples:: count_trading_dates

    Reading the result: The result is an integer count, not a list of dates.

.. py:function:: get_all_trading_dates(market='cn')

    Every session in the calendar.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

    **Examples**

    .. lf-examples:: get_all_trading_dates

    Reading the result: the example prints the number of trading days and the first and last; the full result is a ``DatetimeIndex``, not a DataFrame with security columns.

.. py:function:: get_calendar_coverage(market='cn')

    The authoritative range of the calendar — how far this release has confirmed.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``{"history_start": Timestamp, "confirmed_through": Timestamp}``

    **Examples**

    .. lf-examples:: get_calendar_coverage

    Reading the result: These bounds depend on the data version. Calendar coverage is different from price coverage.

