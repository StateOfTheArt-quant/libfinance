=================
Corporate actions
=================

.. currentmodule:: libfinance

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
    * - :func:`~libfinance.get_ex_factor`
      - Inspect event and cumulative factors

Semantics are covered in :doc:`../data/corporate_actions`. All four functions take
identical arguments. Markets are inferred from security codes; mixed-market requests
are split and merged. Unsupported markets raise an error, not a partial result.

.. py:function:: get_dividends(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Cash dividend events.

    :param order_book_ids: One code or a list
    :param start_date: Start date, filtering on ``ex_date``; omit for the earliest
    :param end_date: End date; omit for the latest
    :param fields: Which columns; omit for all
    :param as_of: Use the information **known** at that point; omit for the latest
    :returns: ``DataFrame`` of events

    Key columns: ``ex_date`` (the price gap happens here), ``record_date``,
    ``payable_date``, ``declaration_date``, ``cash_per_share``,
    ``bonus_per_share``, ``transfer_per_share``.

    **Examples**

    .. lf-examples:: get_dividends

    Reading the result: in turn, the full history, a window with chosen fields, events known by a given day, and both markets in one call; ``order_book_id`` tells the securities apart and ``cash_per_share`` is the cash dividend per share.

.. py:function:: get_splits(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Splits and bonus issues. Arguments as for :py:func:`get_dividends`.

    ``ratio_from`` / ``ratio_to`` read as "``ratio_from`` shares become
    ``ratio_to`` shares".

    **Examples**

    .. lf-examples:: get_splits

    Reading the result: ``ratio_from`` shares become ``ratio_to`` shares (10 to 13 is 3 bonus shares per 10). China's routine bonus and transfer shares are recorded with dividends (``bonus_per_share``, ``transfer_per_share``); China split events come mostly from the 2005–2006 share-structure reform.

.. py:function:: get_allotments(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Rights issues. Arguments as for :py:func:`get_dividends`.

    **Examples**

    .. lf-examples:: get_allotments

    Reading the result: A narrower window can return an empty DataFrame. This is different from a failed query.

.. py:function:: get_spinoffs(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Spin-off events, **US only**. Arguments as for :py:func:`get_dividends`.

    Parent shareholders receive subsidiary shares pro rata. Ex-rights needs an
    amount, but the subsidiary often has no independent market price on the
    ex-date, so ``valuation_price`` is **estimated** — read it together with
    ``valuation_basis`` and ``valuation_source``. ``d_spin_per_share`` is the value
    attributed to each parent share.

    A-share codes yield a "market not bound" error, which is not "no spin-offs in
    this period".

    **Examples**

    .. lf-examples:: get_spinoffs

    Reading the result: read the valuation price together with its basis (``valuation_basis``) and source (``valuation_source``); fields the source did not give are ``None``.

get_ex_factor — Inspect event and cumulative factors
------------------------------------------------------------

.. py:function:: get_ex_factor(order_book_ids, start_date=None, end_date=None)

    Query event factors using complete security codes; mixed CN/US lists are supported.

    :param order_book_ids: One code or a list; the server infers each market
    :param start_date: Inclusive first ex-date; omit for the earliest record
    :param end_date: Inclusive last ex-date; omit for the dataset cutoff. Codes are
        resolved at this business date, or against current identities when omitted
    :returns: DataFrame indexed by ex_date (DatetimeIndex), with order_book_id,
        ex_factor and ex_cum_factor. An empty window for a covered security
        retains the same index and column structure.

    ex_factor is the prior close divided by
    theoretical ex-price, with same-day actions combined. ex_cum_factor is
    calculated from 1 before the security's first event in the dataset release;
    it never restarts at the requested start_date. Unpriced events anywhere in
    the cumulative history raise an error, including events before start_date.
    Unknown securities and coverage errors also propagate.

    See :doc:`../concepts/exfactor` for calculations and charts.

    **Result fields**

    .. list-table::
        :header-rows: 1
        :widths: 24 18 58

        * - Index / column
          - Type
          - Meaning
        * - ``ex_date`` (index)
          - DatetimeIndex
          - Ex-date; multiple securities may have rows on the same date.
        * - ``order_book_id``
          - str
          - Complete security identifier, distinguishing securities and markets.
        * - ``ex_factor``
          - float
          - Event factor for this ex-date, combining same-day actions.
        * - ``ex_cum_factor``
          - float
          - Product of event factors from the security's first event in the
            current dataset release through this row's ex-date.

    CN and US use the same cumulative rule: start at 1 before the first event
    and include the event on the row's date. Coverage differs between securities,
    so cumulative
    levels cannot be used to compare returns across securities. Adjustment ratios
    use cumulative values at two dates for the same security and dataset release.

    **Examples**

    .. lf-examples:: get_ex_factor

    Reading the result: assume the cumulative factor before 2023-07-21 is 5.
    The event factor of 1.04 gives ``5 × 1.04 = 5.2``. Restricting the query to
    July 2023 still returns 5.2, not 1.04. The next event yields
    ``5.2 × 1.05 = 5.46``.

