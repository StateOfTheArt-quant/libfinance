==========
libfinance
==========

\[ English | `中文 <https://libfinance.readthedocs.io/zh-cn/latest/>`_ \]

Conclusions in quantitative research rest on historical data, and historical data is distorted in three common ways: security codes are renamed, reused, and collide across markets; financial statements are revised after release, so a backtest that reads the latest version uses information nobody had at the time; and corporate actions such as dividends and splits break price comparability, so inconsistent adjustment distorts returns. Research and production also tend to run in different languages, Python and C++, and small differences between two interfaces make the same strategy produce different results once it is ported.

``libfinance`` is a financial data client for quantitative research and backtesting, covering Chinese A-shares and US equities, with implementations in Python and C++. It organizes prices, the security catalog, trading calendars, corporate actions, shares, financials, industry / index / theme constituents and daily factors around unified security identifiers, point-in-time data versions and event-by-event adjustment factors. Both markets and both languages follow one interface contract: queries are written the same way, and differences come only from the data.

The data design rests on four conventions:

* **Unified security identifiers**: ``<trading_code>.<namespace>``, such as ``600000.XSHG``,
  ``000001.XSHE`` and ``AAPL.US``. The namespace separates equal codes in different markets, and codes
  resolve at a point in time, so renames and reused codes never land on another security.
* **Point-in-time queries with as_of**: rebuild the security universe of a past date and select the
  financial statements disclosed by then, avoiding look-ahead and survivorship bias.
* **High-quality adjustment factors, exfactor**: computed event by event from corporate actions, with
  unadjusted, forward-adjusted and backward-adjusted prices; ``get_ex_factor`` returns each event's
  factor and the cumulative factor, so every adjustment can be traced.
* **One function design for Python and C++**: both clients implement one contract -- function names,
  parameter order and defaults, validation and errors, returned columns; the same calls are sent
  through both clients to one server and compared item by item.

See :doc:`concepts/security_identifiers`, :doc:`concepts/point_in_time`, :doc:`concepts/exfactor` and
:doc:`concepts/python_cpp`.

.. code-block:: python

    from libfinance import get_price

    # One call, both markets: each code carries its market
    bars = get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05", adjust_type="none")

What this returns and how to read it: :doc:`getting_started/quickstart`.


A-shares and US equities share one vocabulary
=============================================

The unification holds at three layers.

.. list-table::
    :header-rows: 1
    :widths: 22 46 32

    *   - Layer
        - What is shared
        - Example
    *   - Security identifiers
        - Both are written ``<trading_code>.<namespace>``; the granularity of the namespace follows the scope needed to remove ambiguity in that market
        - ``600000.XSHG``, ``AAPL.US``
    *   - Functions and arguments
        - Both markets go through the same functions with the same argument names; ``as_of`` and ``adjust_type`` carry the same meaning
        - ``get_price``, ``instruments``, ``get_dividends``
    *   - Result shape
        - The same columns and the same index; a field that does not apply to a market, or that a deployment does not provide, comes back as ``NaN`` rather than as a separate table
        - ``turnover``, ``limit_up``, ``limit_down`` for US equities

Only queries that do not name a security need the market stated: trading calendars, the full
security master, and coverage ranges. When you query by security, the namespace already carries
the market, and one list may mix the two.

.. code-block:: python

    from libfinance import instruments, get_trading_dates

    instruments(["000001.XSHE", "AAPL.US"])            # the namespace carries the market
    get_trading_dates("2024-01-01", "2024-01-31", market="us")   # no security named

What is shared is the vocabulary and the calling convention; the differences in the data remain.
Allotments are China only, spin-offs US only, and the theme catalogue (THS) China only; US
bars have no price limits, and turnover is not provided for them. See :doc:`howto/us_market` for the picture function by
function.


What data is here
=================

.. list-table::
    :header-rows: 1
    :widths: 24 12 30 34

    *   - Data
        - Markets
        - Main function
        - Notes
    *   - Trading calendar
        - CN · US
        - :func:`~libfinance.get_trading_dates`
        - Sessions, ranges, N sessions forward or back
    *   - Security master
        - CN · US
        - :func:`~libfinance.all_instruments`
        - Code, name, type, listing and delisting dates
    *   - Daily bars
        - CN · US
        - :func:`~libfinance.get_price`
        - OHLC, volume, turnover; adjustable
    *   - Adjustment factors
        - CN · US
        - :func:`~libfinance.get_ex_factor`
        - Event and cumulative factors by ex-date
    *   - Share capital
        - CN · US
        - :func:`~libfinance.get_shares`
        - Per-session total and floating shares
    *   - Dividends / splits / allotments
        - CN · US
        - :func:`~libfinance.get_dividends`
        - Ex-rights events — the source of price gaps; allotments are China only
    *   - Spin-offs
        - US
        - :func:`~libfinance.get_spinoffs`
        - A-shares do not produce this kind of event
    *   - Financial statements (PIT)
        - CN · US
        - :func:`~libfinance.get_pit_financials_ex`
        - Quarterly, with full revision history
    *   - Financial metrics
        - CN · US
        - :func:`~libfinance.get_financial_metrics`
        - Derived financial metrics, per trading day
    *   - Industry classification
        - CN · US
        - :func:`~libfinance.get_instrument_industry`
        - Shenwan, GICS and more; members and weights via :func:`~libfinance.get_industry_constituents`
    *   - Index constituents
        - CN · US
        - :func:`~libfinance.get_index_constituents`
        - CSI, S&P and more; weights via :func:`~libfinance.get_index_weights`
    *   - Themes
        - CN
        - :func:`~libfinance.get_theme_constituents`
        - THS themes; weights via :func:`~libfinance.get_theme_weights`
    *   - Daily factors
        - CN
        - :func:`~libfinance.get_factor_exposure`
        - alpha158, qlib, Barra CNE5 / CNE6; libraries and names via :func:`~libfinance.list_factor_libraries`
    *   - Live quotes
        - CN
        - :class:`~libfinance.subscribe.quote_api.QuoteApi`
        - Streaming subscription

How far back the history goes and how recent it is depend on the service you
connect to. **Do not copy dates out of these docs** — ask the service, as shown
in :doc:`data/freshness`.


Where to start
==============

.. grid:: 1 1 3 3
    :gutter: 3

    .. grid-item-card:: I just want some prices
        :link: getting_started/quickstart
        :link-type: doc

        Install, connect, run your first query. Then read
        :doc:`howto/price_panel`, which walks through every trap in
        "give me the last N sessions".

    .. grid-item-card:: I am building a backtest
        :link: concepts/point_in_time
        :link-type: doc

        Start with :doc:`concepts/point_in_time` and :doc:`concepts/exfactor`.
        Together they decide whether your backtest sees numbers that did not
        exist at the time.

    .. grid-item-card:: I want live data
        :link: data/realtime
        :link-type: doc

        Snapshot queries and streaming subscriptions are two different paths.
        :doc:`howto/subscribe` has a program you can run as-is.

Already using it and something looks wrong? Go straight to
:doc:`howto/troubleshooting` — it is organised by **symptom**.


Three things worth knowing up front
===================================

These are not advanced topics. They are **defaults**. Not knowing them means your
code runs fine and your numbers are wrong.

.. dropdown:: Without ``adjust_type``, you get forward-adjusted prices
    :color: warning
    :icon: alert

    Same stock, same day: forward-adjusted close 8.81, unadjusted 10.49 — a 16%
    difference. Use ``adjust_type`` to select the price convention explicitly.
    See :doc:`data/price`.

.. dropdown:: ``end_date`` cannot be today
    :color: warning
    :icon: alert

    The calendar is published ahead of time (it reaches the end of the year);
    price data only reaches the **last closed session**. Passing today is
    rejected outright rather than silently returning a shorter table.
    See :doc:`data/freshness`.

.. dropdown:: Financial statements get restated
    :color: warning
    :icon: alert

    One company's Q2 2024 net profit exists here in five versions, the latest
    published in 2026. Omit ``as_of`` in a backtest and you are using numbers
    from the future. See :doc:`data/point_in_time`.


.. toctree::
    :maxdepth: 2
    :caption: Getting started
    :hidden:

    getting_started/installation
    getting_started/quickstart

.. toctree::
    :maxdepth: 1
    :caption: Concepts
    :titlesonly:
    :hidden:

    concepts/security_identifiers
    concepts/point_in_time
    concepts/exfactor
    concepts/python_cpp

.. toctree::
    :maxdepth: 2
    :caption: API reference
    :hidden:

    reference/contracts
    reference/market_data
    reference/fundamentals
    reference/classification
    5 Corporate actions <reference/corporate_actions>
    6 Real-time quotes <reference/realtime>
    7 Factors <reference/factors>

.. toctree::
    :maxdepth: 1
    :caption: Lookup and troubleshooting
    :hidden:

    reference/fields
    reference/errors

.. toctree::
    :maxdepth: 1
    :caption: About
    :hidden:

    about/changelog
    about/contributing
    about/citing
