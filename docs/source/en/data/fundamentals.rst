==============================
Financials and share capital
==============================

Financial statements come **by quarter**; derived metrics and share capital come **by trading day**.
This chapter covers their semantics and units; every function's parameters and examples with their real
output are in :doc:`../reference/financials` and :doc:`../reference/shares`.

Financial statements: :func:`~libfinance.get_pit_financials_ex`
===============================================================

.. code-block:: python

    import libfinance as lf

    lf.get_pit_financials_ex("600000.XSHG", ["total_operating_revenue", "net_income_parent"], "2024q1", "2024q3")

The table is indexed by ``(order_book_id, quarter)``. Besides the fields asked for it has two columns:

- ``info_date``: when this version of the statement was disclosed;
- ``if_adjusted``: ``1`` when this version is a later restatement, ``0`` for the first disclosure.

China and US securities use the same field names (``net_income_parent``, ``assets`` ...).

Arguments:

.. list-table::
    :header-rows: 1
    :widths: 24 76

    *   - Argument
        - Notes
    *   - ``order_book_ids``
        - One code or a list
    *   - ``fields``
        - Which financial fields; required
    *   - ``start_quarter`` / ``end_quarter``
        - Quarter range, like ``"2024q1"``
    *   - ``as_of``
        - Which day you are looking back from. **Required in backtests** — see
          :doc:`point_in_time`
    *   - ``statements``
        - ``"latest"`` (default, one row per quarter) or ``"all"`` (every revision)

.. important::

    Without ``as_of`` each quarter is its **latest** version: a quarter may come back as the restatement
    published a year later (``info_date`` the next year, ``if_adjusted`` 1), not the version first disclosed.
    **Backtests must pass** ``as_of``; see :doc:`point_in_time`.

Derived metrics: :func:`~libfinance.get_financial_metrics`
==========================================================

Metrics computed from the statements (``roe_lf``, ``revenue_ttm``, ``net_profit_growth_lyr``,
``debt_to_assets_lf`` ...), **one value per trading day**, on the same formulas for China and the US:

.. code-block:: python

    lf.get_financial_metrics("600519.XSHG", ["roe_lf", "revenue_ttm"], "2024-10-28", "2024-11-01")

A trading day's value comes from **the latest report visible after that day's close**: values step on
announcement days and hold in between. It is point-in-time by construction, so there is no ``as_of``
parameter. Without dates it answers for the latest trading day. An unknown metric name is refused
explicitly, never answered with an empty column.

Share capital: :func:`~libfinance.get_shares`
=============================================

Share capital comes as a **panel by trading day**: share changes are sparse events, expanded here to
every trading day so they line up with prices. China and the US use the same fields:

.. code-block:: python

    lf.get_shares(["000001.XSHE", "600000.XSHG"], "2024-06-24", "2024-06-28",
                  fields=["issued_shares", "tradable_shares"])

Columns and units
-----------------

.. list-table::
    :header-rows: 1
    :widths: 26 74

    * - Field
      - Meaning
    * - ``issued_shares``
      - Shares issued (total share capital, company level)
    * - ``tradable_shares``
      - Tradable shares (for China, tradable A shares)
    * - ``restricted_shares``
      - Restricted (non-tradable) shares
    * - ``free_float_shares``
      - Free float: shares left after restricted and controlling holdings (a vendor estimate for China)
    * - ``preferred_shares``
      - Preferred shares
    * - ``shares_outstanding``
      - Shares outstanding (security level; for the US from SEC and CRSP). China's total share capital is
        **not** taken as this, so it is ``NaN`` for China

.. important::

    **Every share field is in shares**, not in ten-thousands or hundred-millions.

    Market cap is ``shares x price``, with the **unadjusted** price (``adjust_type="none"``): adjusted
    prices are not on the scale of today's share count.

Omitting ``start_date`` / ``end_date`` returns the whole history; pass a window and fields when you can.
