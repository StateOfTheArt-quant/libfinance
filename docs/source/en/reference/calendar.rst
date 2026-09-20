================
Trading calendar
================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/calendar`. Every function takes ``market``,
defaulting to ``"cn"``.

.. py:function:: get_trading_dates(start_date, end_date, market='cn')

    Sessions within a range.

    :param start_date: Start date (calendar date)
    :param end_date: End date (calendar date)
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex`` of sessions
    :raises CalendarCoverageError: if either endpoint falls outside the confirmed range

    .. code-block:: python

        >>> get_trading_dates("2024-05-11", "2024-05-20")
        DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                       '2024-05-17', '2024-05-20'],
                      dtype='datetime64[ns]', freq=None)

.. py:function:: is_trading_date(date, market='cn')

    Whether a given day is a session.

    :param date: The day to test
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``bool``

.. py:function:: get_previous_trading_date(date, n=1, market='cn')

    The n-th session before a given day.

    :param date: Reference day
    :param n: How many sessions back
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping back goes past the start of the range

    .. code-block:: python

        >>> get_previous_trading_date("2020-05-18", n=3)
        Timestamp('2020-05-13 00:00:00')

.. py:function:: get_next_trading_date(date, n=1, market='cn')

    The n-th session after a given day.

    :param date: Reference day
    :param n: How many sessions forward
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping forward goes past the confirmed end

.. py:function:: get_n_trading_dates_until(date, n, market='cn')

    The last n sessions up to and including a given day.

    :param date: Last day (inclusive)
    :param n: How many sessions
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

.. py:function:: count_trading_dates(start_date, end_date, market='cn')

    How many sessions fall in a range.

    :param start_date: Start date
    :param end_date: End date
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``int``

.. py:function:: get_all_trading_dates(market='cn')

    Every session in the calendar.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

.. py:function:: get_calendar_coverage(market='cn')

    The authoritative range of the calendar — how far this release has confirmed.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``{"history_start": Timestamp, "confirmed_through": Timestamp}``

    .. code-block:: python

        >>> get_calendar_coverage()
        {'history_start': Timestamp('1990-12-19 00:00:00'),
         'confirmed_through': Timestamp('2026-12-31 00:00:00')}
