1 Instruments and trading calendars
======================================================================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.all_instruments`
      - List securities by market, type and historical date
    * - :func:`~libfinance.instruments`
      - Resolve one or more codes, including mixed markets
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

.. toctree::
    :maxdepth: 2

    instrument
    calendar
    index_meta
