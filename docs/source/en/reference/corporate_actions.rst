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

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_dividends.1]
        :end-before: # [/get_dividends.1]
        :prepend: from libfinance import get_dividends

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_dividends.1.txt
        :language: text

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_dividends.2]
        :end-before: # [/get_dividends.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_dividends.2.txt
        :language: text

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_dividends.3]
        :end-before: # [/get_dividends.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_dividends.3.txt
        :language: text

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_dividends.4]
        :end-before: # [/get_dividends.4]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_dividends.4.txt
        :language: text


    Reading the result: The blocks illustrate full history, field selection, a knowledge cutoff, and mixed-market results identified by order_book_id. The numbers are not actual dividends for these securities.

    :download:`Download the full example <../../../../example/corporate_actions.py>`

.. py:function:: get_splits(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Splits and bonus issues. Arguments as for :py:func:`get_dividends`.

    ``ratio_from`` / ``ratio_to`` read as "``ratio_from`` shares become
    ``ratio_to`` shares".

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_splits.1]
        :end-before: # [/get_splits.1]
        :prepend: from libfinance import get_splits

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_splits.1.txt
        :language: text

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_splits.2]
        :end-before: # [/get_splits.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_splits.2.txt
        :language: text

    Reading the result: ratio_from shares become ratio_to shares. Illustrated events explain the structure only.

    :download:`Download the full example <../../../../example/corporate_actions.py>`

.. py:function:: get_allotments(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Rights issues. Arguments as for :py:func:`get_dividends`.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_allotments.1]
        :end-before: # [/get_allotments.1]
        :prepend: from libfinance import get_allotments

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_allotments.1.txt
        :language: text

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_allotments.2]
        :end-before: # [/get_allotments.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_allotments.2.txt
        :language: text

    Reading the result: A narrower window can return an empty DataFrame. This is different from a failed query.

    :download:`Download the full example <../../../../example/corporate_actions.py>`

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

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/corporate_actions.py
        :language: python
        :start-after: # [get_spinoffs.1]
        :end-before: # [/get_spinoffs.1]
        :prepend: from libfinance import get_spinoffs

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_spinoffs.1.txt
        :language: text

    Reading the result: Read the valuation price together with its basis and source. Illustrated values are not actual spin-off terms.

    :download:`Download the full example <../../../../example/corporate_actions.py>`


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

    These outputs illustrate structure only. Values and events are not actual
    market data and must not be used for investment calculations.

    .. literalinclude:: ../../../../example/4b_exfactor.py
        :language: python
        :start-after: # [get_ex_factor.1]
        :end-before: # [/get_ex_factor.1]
        :prepend: from libfinance import get_ex_factor

    Illustrative output:

    .. literalinclude:: ../../../_shared/example_outputs/get_ex_factor.1.txt
        :language: text

    .. literalinclude:: ../../../../example/4b_exfactor.py
        :language: python
        :start-after: # [get_ex_factor.2]
        :end-before: # [/get_ex_factor.2]

    Illustrative output:

    .. literalinclude:: ../../../_shared/example_outputs/get_ex_factor.2.txt
        :language: text

    Reading the result: assume the cumulative factor before 2023-07-21 is 5.
    The event factor of 1.04 gives ``5 × 1.04 = 5.2``. Restricting the query to
    July 2023 still returns 5.2, not 1.04. The next event yields
    ``5.2 × 1.05 = 5.46``.

    .. literalinclude:: ../../../../example/4b_exfactor.py
        :language: python
        :start-after: # [get_ex_factor.3]
        :end-before: # [/get_ex_factor.3]

    Illustrative output:

    .. literalinclude:: ../../../_shared/example_outputs/get_ex_factor.3.txt
        :language: text

    :download:`Download example <../../../../example/4b_exfactor.py>`
