=================
Corporate actions
=================

Dividends, bonus issues, allotments, spin-offs — these events are **the source of
price gaps**, and the reason adjustment factors exist. When a stock appears to
"crash 10%" one day with no news behind it, check here whether that day was an
ex-rights date.

The four functions take identical arguments and differ only in the event type:

.. list-table::
    :header-rows: 1
    :widths: 34 14 52

    *   - Function
        - Markets
        - Event
    *   - :func:`~libfinance.get_dividends`
        - CN · US
        - Cash dividends
    *   - :func:`~libfinance.get_splits`
        - CN · US
        - Splits and bonus issues
    *   - :func:`~libfinance.get_allotments`
        - CN · US
        - Rights issues
    *   - :func:`~libfinance.get_spinoffs`
        - **US only**
        - Spin-offs

Dividends
=========

.. code-block:: python

    >>> from libfinance import get_dividends
    >>> get_dividends("600000.XSHG", start_date="2023-01-01", end_date="2026-09-01")

.. code-block:: text

      order_book_id    ex_date dist_kind   marker cash_per_share currency  \
    0   600000.XSHG 2023-07-21      CASH  REGULAR           0.32      CNY
    1   600000.XSHG 2024-07-18      CASH  REGULAR          0.321      CNY
    2   600000.XSHG 2025-07-16      CASH  REGULAR           0.41      CNY
    3   600000.XSHG 2026-07-16      CASH  REGULAR           0.42      CNY

      bonus_per_share transfer_per_share  declaration_date record_date payable_date
    0             0.0                0.0        2023-07-13  2023-07-20   2023-07-21
    ...

Key columns:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``ex_date``
        - **Ex-dividend date**. The price gap happens on this day
    *   - ``record_date``
        - Record date — hold through this close to be entitled
    *   - ``payable_date``
        - Payment date
    *   - ``declaration_date``
        - Announcement date
    *   - ``cash_per_share``
        - Cash paid per share
    *   - ``bonus_per_share`` / ``transfer_per_share``
        - Bonus shares / capitalisation shares per share

Splits and bonus issues
=======================

.. code-block:: python

    >>> from libfinance import get_splits
    >>> get_splits("600000.XSHG", start_date="2000-01-01", end_date="2026-09-01")
      order_book_id    ex_date event_type ratio_from ratio_to record_date payable_date
    0   600000.XSHG 2006-05-12      SPLIT       10.0     13.0  2006-05-10   2006-05-12

Read ``ratio_from`` / ``ratio_to`` as "10 shares become 13 shares".

Spin-offs (US only)
===================

Parent-company shareholders receive shares in a subsidiary pro rata. A-share
carve-outs follow a different process and do not produce this kind of ex-rights
event.

.. warning::

    Calling :func:`~libfinance.get_spinoffs` with A-share codes yields a "market
    not bound" error, **not** "no spin-offs in this period". Those mean entirely
    different things.

Read the valuation columns together with their basis: ex-rights needs an amount,
but on the ex-date the subsidiary often has no independent market price, so
``valuation_price`` is **estimated**.

.. list-table::
    :header-rows: 1
    :widths: 30 70

    *   - Column
        - Meaning
    *   - ``valuation_price``
        - Estimated price of the subsidiary shares
    *   - ``valuation_basis``
        - Which basis the estimate uses
    *   - ``valuation_source``
        - Where the valuation comes from
    *   - ``d_spin_per_share``
        - Spin-off value attributed to each parent share
    *   - ``ratio_child_per_parent``
        - Subsidiary shares received per parent share

Taking ``valuation_price`` without reading the last two assumes a basis the data
never claimed.

Shared arguments
================

.. list-table::
    :header-rows: 1
    :widths: 22 78

    *   - Argument
        - Notes
    *   - ``order_book_ids``
        - One code or a list
    *   - ``start_date`` / ``end_date``
        - Filter on ``ex_date``; omit for the full history
    *   - ``fields``
        - Restrict columns; omit for all
    *   - ``as_of``
        - Use the information **known** at that point. Corporate actions are also
          revised and cancelled, so backtests should pass it — see
          :doc:`point_in_time`
    *   - ``market``
        - Omit to use the server default

Relationship to adjustment
==========================

These events are what adjustment factors are built from. For everyday research you
do **not** need to apply them yourself — use ``adjust_type`` on
:func:`~libfinance.get_price` (see :doc:`price`).

You need the raw events when you want to:

* identify which event caused a particular price gap;
* study the events themselves (event studies);
* implement a bespoke adjustment convention.
