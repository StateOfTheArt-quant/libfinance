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
        * - :func:`~libfinance.get_financial_metrics`
          - Read derived financial metrics on each trading day
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
        * - :func:`~libfinance.get_instrument_industry`
          - Map securities to their industries at a date
        * - :func:`~libfinance.get_industry_constituents`
          - Find the securities in an industry at a date
        * - :func:`~libfinance.get_industry_weights`
          - Read an industry's constituent weights, with their methodology
        * - :func:`~libfinance.get_instrument_indices`
          - Map securities to the indices they belong to at a date
        * - :func:`~libfinance.get_index_constituents`
          - Find the securities in an index at a date
        * - :func:`~libfinance.get_index_weights`
          - Read an index's constituent weights, with their methodology
        * - :func:`~libfinance.get_instrument_themes`
          - Map securities to the themes they belong to at a date
        * - :func:`~libfinance.get_theme_constituents`
          - Find the securities in a theme at a date
        * - :func:`~libfinance.get_theme_weights`
          - Read a theme's constituent weights, with their methodology

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

.. dropdown:: 7 Factors
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - Function / class
          - Purpose
        * - :func:`~libfinance.get_factor_exposure`
          - Read factor exposures (qlib, alpha158, Barra CNE5)
        * - :func:`~libfinance.list_factor_libraries`
          - The factor libraries, their versions and factor counts
        * - :func:`~libfinance.list_factors`
          - The factors of one library

    :doc:`factors`

Lookup and troubleshooting
----------------------------------------

:doc:`fields` · :doc:`errors`
