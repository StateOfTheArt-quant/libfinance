:orphan:

API reference
========================================

Expand a topic to find a function by the problem it solves. Follow its link for parameters, returns and examples.
Example dates must fall within the coverage of your service.

.. dropdown:: 1 Instruments and trading calendars
    :color: primary
    :icon: book

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

    :doc:`contracts`

.. dropdown:: 2 Market data
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_price`
          - Read daily bars with field and adjustment choices
        * - :func:`~libfinance.get_price_coverage`
          - Find the last covered price date

    :doc:`market_data`

.. dropdown:: 3 Fundamentals
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_pit_financials_ex`
          - Read quarterly statements and their visible revisions
        * - :func:`~libfinance.get_factor`
          - Read derived financial factors
        * - :func:`~libfinance.get_shares`
          - Read historical share capital

    :doc:`fundamentals`

.. dropdown:: 4 Industries and concepts
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_industry_mapping`
          - Discover industry codes and hierarchy
        * - :func:`~libfinance.get_instrument_industry`
          - Map securities to industries at a date
        * - :func:`~libfinance.get_industry`
          - Find securities belonging to an industry
        * - :func:`~libfinance.get_index_weights`
          - Read index constituents and weights at a trading date
        * - :func:`~libfinance.get_concept_meta`
          - Discover concept names and identifiers
        * - :func:`~libfinance.get_concept_weights`
          - Read concept constituents as known at a cutoff

    :doc:`classification`

.. dropdown:: 5 Corporate actions
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_dividends`
          - Read dividend events
        * - :func:`~libfinance.get_splits`
          - Read split ratios
        * - :func:`~libfinance.get_allotments`
          - Read allotment events
        * - :func:`~libfinance.get_spinoffs`
          - Read US spin-offs and valuation information

    :doc:`corporate_actions`

.. dropdown:: 6 Real-time quotes
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_last_quotes`
          - Read the latest quote snapshots
        * - :class:`~libfinance.subscribe.quote_api.QuoteApi`
          - Connect, subscribe and unsubscribe
        * - :class:`~libfinance.subscribe.quote_api.QuoteSpi`
          - Handle subscription responses and quotes

    :doc:`realtime`

Lookup and troubleshooting
----------------------------------------

:doc:`fields` · :doc:`errors`
