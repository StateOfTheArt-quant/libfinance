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

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_trading_dates.1]
        :end-before: # [/get_trading_dates.1]
        :prepend: from libfinance import get_trading_dates

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_trading_dates.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_trading_dates.2]
        :end-before: # [/get_trading_dates.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_trading_dates.2.txt
        :language: text

    Reading the result: The same range can contain different trading dates in different markets; January 15 illustrates the difference here.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: is_trading_date(date, market='cn')

    Whether a given day is a session.

    :param date: The day to test
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``bool``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [is_trading_date.1]
        :end-before: # [/is_trading_date.1]
        :prepend: from libfinance import is_trading_date

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/is_trading_date.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [is_trading_date.2]
        :end-before: # [/is_trading_date.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/is_trading_date.2.txt
        :language: text

    Reading the result: The boolean result can be used directly in a condition.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: get_previous_trading_date(date, n=1, market='cn')

    The n-th session before a given day.

    :param date: Reference day
    :param n: How many sessions back
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping back goes past the start of the range

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_previous_trading_date.1]
        :end-before: # [/get_previous_trading_date.1]
        :prepend: from libfinance import get_previous_trading_date

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_previous_trading_date.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_previous_trading_date.2]
        :end-before: # [/get_previous_trading_date.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_previous_trading_date.2.txt
        :language: text

    Reading the result: Both offsets exclude the input date. n counts trading days, not calendar days.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: get_next_trading_date(date, n=1, market='cn')

    The n-th session after a given day.

    :param date: Reference day
    :param n: How many sessions forward
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``Timestamp``
    :raises CalendarCoverageError: if stepping forward goes past the confirmed end

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_next_trading_date.1]
        :end-before: # [/get_next_trading_date.1]
        :prepend: from libfinance import get_next_trading_date

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_next_trading_date.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_next_trading_date.2]
        :end-before: # [/get_next_trading_date.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_next_trading_date.2.txt
        :language: text

    Reading the result: The first trading day after Friday is Monday; n=3 moves to the third trading day.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: get_n_trading_dates_until(date, n, market='cn')

    The last n sessions up to and including a given day.

    :param date: Last day (inclusive)
    :param n: How many sessions
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_n_trading_dates_until.1]
        :end-before: # [/get_n_trading_dates_until.1]
        :prepend: from libfinance import get_n_trading_dates_until

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_n_trading_dates_until.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_n_trading_dates_until.2]
        :end-before: # [/get_n_trading_dates_until.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_n_trading_dates_until.2.txt
        :language: text

    Reading the result: A trading-day cutoff includes that day. A Sunday cutoff ends at the preceding Friday.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: count_trading_dates(start_date, end_date, market='cn')

    How many sessions fall in a range.

    :param start_date: Start date
    :param end_date: End date
    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``int``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [count_trading_dates.1]
        :end-before: # [/count_trading_dates.1]
        :prepend: from libfinance import count_trading_dates

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/count_trading_dates.1.txt
        :language: text

    Reading the result: The result is an integer count, not a list of dates.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: get_all_trading_dates(market='cn')

    Every session in the calendar.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``DatetimeIndex``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_all_trading_dates.1]
        :end-before: # [/get_all_trading_dates.1]
        :prepend: from libfinance import get_all_trading_dates

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_all_trading_dates.1.txt
        :language: text

    Reading the result: The result is a date index, not a DataFrame with security columns.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`

.. py:function:: get_calendar_coverage(market='cn')

    The authoritative range of the calendar — how far this release has confirmed.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``{"history_start": Timestamp, "confirmed_through": Timestamp}``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_calendar_coverage.1]
        :end-before: # [/get_calendar_coverage.1]
        :prepend: from libfinance import get_calendar_coverage

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_calendar_coverage.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0b_trading_calendar.py
        :language: python
        :start-after: # [get_calendar_coverage.2]
        :end-before: # [/get_calendar_coverage.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_calendar_coverage.2.txt
        :language: text

    Reading the result: These bounds depend on the data version. Calendar coverage is different from price coverage.

    :download:`Download the full example <../../../../example/0b_trading_calendar.py>`
