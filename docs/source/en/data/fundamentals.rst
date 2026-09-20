==============================
Financials and share capital
==============================

Financial data is fetched **by quarter**; share capital is fetched **by session**.
This chapter covers their semantics and units.

Financial statements
====================

.. code-block:: python

    >>> from libfinance import get_pit_financials_ex
    >>> get_pit_financials_ex("600000.XSHG", ["net_profit"], "2024q1", "2024q4")
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    600000.XSHG   2024q1  2025-04-30  1.766000e+10            1
                  2024q2  2026-08-28  2.732400e+10            1
                  2024q3  2025-10-31  3.568700e+10            1
                  2024q4  2026-08-28  4.583500e+10            1

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

    Note the ``info_date`` on the 2024q1 row above: **2025-04-30**. That is a
    revision published a year later, not the figure first reported in April 2024.
    Omitting ``as_of`` gives you this.

Financial factors
=================

Metrics derived on top of statement line items, also quarterly:

.. code-block:: python

    >>> from libfinance import get_factor
    >>> get_factor("600000.XSHG", ["net_profit_ttm"], "2024q1", "2025q1")
                           net_profit_ttm
    order_book_id quarter
    600000.XSHG   2024q1     1.072960e+11
                  2024q2     1.110050e+11
                  2024q3     1.181000e+11
                  2024q4     1.265060e+11
                  2025q1     1.266220e+11

``as_of`` behaves exactly as in :func:`~libfinance.get_pit_financials_ex`.

Available factor names come from the server and vary by deployment. An unknown
factor name is rejected explicitly rather than returned as an empty column.

Share capital
=============

Unlike financials, share capital comes back as a **per-session panel**. Share
count changes are sparse events, but they are expanded onto every session so the
result aligns directly with price data:

.. code-block:: python

    >>> from libfinance import get_shares
    >>> get_shares("600000.XSHG", start_date="2024-01-01", end_date="2024-01-05")

.. code-block:: text

                              circulation_a free_circulation non_circulation_a  \
    order_book_id date
    600000.XSHG   2024-01-02  29352176396.0    10802151287.0               0.0
                  2024-01-03  29352176396.0    10802151287.0               0.0
                  2024-01-04  29352176848.0    10802151287.0               0.0
                  2024-01-05  29352176848.0    10802151287.0               0.0

                             preferred_shares          total        total_a
    order_book_id date
    600000.XSHG   2024-01-02              0.0  29352176396.0  29352176396.0
    ...

Columns and units
-----------------

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``total``
        - Total shares
    *   - ``total_a``
        - Total A-shares
    *   - ``circulation_a``
        - Floating A-shares
    *   - ``non_circulation_a``
        - Non-floating A-shares
    *   - ``free_circulation``
        - Free-float shares (excluding lock-ups, control blocks and so on)
    *   - ``preferred_shares``
        - Preferred shares

.. important::

    **Every share column is in shares** — not tens of thousands, not millions.

    Market capitalisation is ``shares × price``. Use the **unadjusted** price
    (``adjust_type="none"``) — adjusted prices are not on the same basis as the
    current share count.

Omitting ``start_date`` / ``end_date`` returns the entire history from the first
share event to the last, which is sizeable; prefer an explicit range.

For a subset of columns:

.. code-block:: python

    >>> get_shares(["000001.XSHE", "600000.XSHG"],
    ...            start_date="2024-01-01", end_date="2024-06-30",
    ...            fields=["total", "circulation_a"])

.. note::

    Share capital is **A-share only**. Calling it with US codes returns
    "namespace 'shares' has no provider for market='us'".
