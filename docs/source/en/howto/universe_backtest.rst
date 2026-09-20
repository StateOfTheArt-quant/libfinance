==================================
Building a historical universe
==================================

**Goal**: build "the banks inside the CSI 300 on 2024-03-08" without leaking
future information.

There is really only one rule: **pass the date at every step**. Omitting it means
slicing the past with today's constituents and today's industry classification —
which is look-ahead bias.

Full example
============

.. code-block:: python

    from libfinance import get_index_weights, get_instrument_industry, get_price

    AS_OF = "2024-03-08"

    # 1. Constituents and weights on that day
    w = get_index_weights(index_code="000300.XSHG", date=AS_OF)

    # 2. Industry membership on that day (note date=AS_OF, not today)
    ind = get_instrument_industry(list(w["order_book_id"]), date=AS_OF)

    # 3. Keep the banks
    banks = ind[ind["first_industry_name"] == "银行"].index.tolist()

    # 4. Attach the weights
    sub = w[w["order_book_id"].isin(banks)].sort_values("weight", ascending=False)

A real run:

.. code-block:: text

    >>> len(w), w["weight"].sum()
    (300, 1.0)

    >>> ind["first_industry_name"].value_counts().head(5)
    电子      30
    电力设备    29
    非银金融    27
    医药生物    24
    银行      22

    >>> len(banks)
    22

    >>> sub.head(3)
     index_code       date order_book_id  weight
    000300.XSHG 2024-03-08   600036.XSHG 0.02225
    000300.XSHG 2024-03-08   601166.XSHG 0.01358
    000300.XSHG 2024-03-08   601398.XSHG 0.01048

Then fetch prices for that set:

.. code-block:: python

    px = get_price(banks, "2024-03-01", "2024-03-08")["close"].unstack("order_book_id")

Three lenses
============

.. list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - Lens
        - Function
        - Notes
    *   - Index constituents
        - :func:`~libfinance.get_index_weights`
        - Works on any trading day, not just rebalancing dates. Weights normalised
    *   - Industry
        - :func:`~libfinance.get_industry`
        - Pass ``date``; ``level`` selects the depth
    *   - Concept sectors
        - :func:`~libfinance.get_concept_weights`
        - Look ``concept_id`` up via :func:`~libfinance.get_concept_meta`;
          hard-coded ids go stale

To take an industry across the whole market rather than within an index:

.. code-block:: python

    >>> from libfinance import get_industry
    >>> get_industry("480000", date="2024-03-08")[:4]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE']

Verifying there is no leakage
=============================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    *   - Check
        - Expected
    *   - The ``date`` column in the weights
        - Equal to (or earlier than) the day you asked for
    *   - Constituent count
        - Matches the index size (300 for the CSI 300)
    *   - Weights summed
        - Approximately 1
    *   - Any name not yet listed at that date
        - Cross-check ``listed_date`` via :func:`~libfinance.instruments` with ``date=``

.. warning::

    **Never hard-code a universe.** Index membership is rebalanced, industry
    mappings change, concept sectors are created and retired. Re-fetch on every
    backtest date — that is what "the universe at the time" means.

Rolling construction
====================

To rebuild monthly, fetch again on each rebalancing date:

.. code-block:: python

    from libfinance import get_trading_dates, get_index_weights

    dates = get_trading_dates("2024-01-01", "2024-06-30")
    rebalance = [d for d in dates if d.day <= 5][:6]   # start of each month

    universe = {}
    for d in rebalance:
        day = d.strftime("%Y-%m-%d")
        universe[day] = get_index_weights(index_code="000300.XSHG", date=day)

Look-ahead bias in financial data is a separate topic — see :doc:`pit_backtest`.
