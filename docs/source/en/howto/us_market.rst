======================
Working with US stocks
======================

**Goal**: know what US data is available, how calls differ from China A-shares, and which data only one
market has.

Three differences
=================

1. **Codes end in** ``.US``: ``AAPL.US``, ``NVDA.US``, the index ``SPX.US``.
2. **Queries that name no security take** ``market="us"``: the trading calendar, the catalog, price coverage.
3. **Queries by security take no market**: the code already says which market, and one list may mix China
   and US codes.

.. code-block:: python

    import libfinance as lf

    lf.get_trading_dates("2024-01-01", "2024-01-31", market="us")   # market needed
    lf.all_instruments(market="us")                                 # market needed
    lf.get_price(["AAPL.US", "600000.XSHG"], "2026-03-02", "2026-03-06")   # not needed

What has US data
================

.. list-table::
    :header-rows: 1
    :widths: 40 12 48

    * - Function
      - US
      - Notes
    * - Calendar functions (:func:`~libfinance.get_trading_dates` ...)
      - ✅
      - Pass ``market="us"``
    * - :func:`~libfinance.all_instruments` / :func:`~libfinance.instruments`
      - ✅
      - Stocks, indices, industries (GICS, ICB, NAICS, SIC); the theme catalogue is China only
    * - :func:`~libfinance.get_price` / :func:`~libfinance.get_price_coverage`
      - ✅
      - Stocks and indices; ``turnover``, ``limit_up`` and ``limit_down`` are ``NaN`` (see below)
    * - :func:`~libfinance.get_ex_factor`
      - ✅
      -
    * - :func:`~libfinance.get_dividends` / :func:`~libfinance.get_splits`
      - ✅
      -
    * - :func:`~libfinance.get_spinoffs`
      - ✅
      - **US only**; a China code is refused explicitly
    * - :func:`~libfinance.get_allotments`
      - ❌
      - **China only** (rights issues); a US code is refused explicitly
    * - :func:`~libfinance.get_shares`
      - ✅
      - The same fields as China; see :doc:`../data/fundamentals`
    * - :func:`~libfinance.get_pit_financials_ex` / :func:`~libfinance.get_financial_metrics`
      - ✅
      - The same fields and formulas as China
    * - Industries: :func:`~libfinance.get_instrument_industry` ...
      - ✅
      - Classifications GICS, ICB, NAICS, SIC (``source="GICS"``)
    * - Indices: :func:`~libfinance.get_instrument_indices` ...
      - ✅
      - e.g. ``SPX.US``
    * - Themes: :func:`~libfinance.get_instrument_themes` ...
      - ❌
      - The theme catalogue (THS) is China only; a US code answers an empty table

For data only one market has, a code of the other market is **refused explicitly**, naming where that data
is published; it never answers an empty table that would read as "no events":

.. code-block:: text

    RpcError(code=2001): ['AAPL.US'] are ['US'] securities; allotments are published for ['CN'] only

An empty table in a supported market (Apple has no spin-off, say) **does** mean "no events". Keep the two apart.

Three empty price columns
=========================

``get_price`` returns the same columns for US stocks as for China, but ``turnover``, ``limit_up`` and
``limit_down`` are ``NaN``: US stocks have no price limits, and turnover is not provided. Estimate traded
value with ``close * volume`` when you need it. Examples with their real output are in
:doc:`../reference/price`.

How far the data goes
=====================

US and China coverage end **separately**. ``get_price_coverage(market="us")`` answers by security type:
stocks under ``stock`` (keyed ``US``), indices under ``index`` (by exchange). End a recent window at the
matching ``end`` rather than at today; see :doc:`../data/freshness`.

Names are full English names
============================

A US security's ``name`` is its full English name with the security class (``Apple Inc. - Common Stock``),
not the ticker; the ticker is the ``order_book_id`` without ``.US``.

Field meanings are in :doc:`../data/corporate_actions`.
