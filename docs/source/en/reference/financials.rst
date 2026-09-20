===============
Financial data
===============

.. currentmodule:: libfinance

Security-code queries infer the market on the server and accept no market argument. Unsupported markets raise an error.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_pit_financials_ex`
      - Read quarterly statements and their visible revisions
    * - :func:`~libfinance.get_factor`
      - Read derived financial factors


Semantics are covered in :doc:`../data/fundamentals`; ``as_of`` in
:doc:`../data/point_in_time`.

.. py:function:: get_pit_financials_ex(order_book_ids, fields, start_quarter, end_quarter, as_of=None, statements='latest')

    Point-in-time financial statement data.

    :param order_book_ids: One code or a list
    :param fields: Which financial fields; required
    :param start_quarter: First quarter, like ``"2024q1"``
    :param end_quarter: Last quarter
    :param as_of: Use the version **known** at that point; omit for the latest.
        **Pass this in backtests**, or you will use restatements that had not been
        published yet.
    :param statements: ``"latest"`` (one row per quarter) or ``"all"`` (every
        revision)
    :returns: ``DataFrame`` indexed by ``(order_book_id, quarter)``, with
        ``info_date`` and ``if_adjusted`` alongside the requested fields

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/2_financials.py
        :language: python
        :start-after: # [get_pit_financials_ex.1]
        :end-before: # [/get_pit_financials_ex.1]
        :prepend: from libfinance import get_pit_financials_ex

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.1.txt
        :language: text

    .. literalinclude:: ../../../../example/2_financials.py
        :language: python
        :start-after: # [get_pit_financials_ex.2]
        :end-before: # [/get_pit_financials_ex.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.2.txt
        :language: text

    .. literalinclude:: ../../../../example/2_financials.py
        :language: python
        :start-after: # [get_pit_financials_ex.3]
        :end-before: # [/get_pit_financials_ex.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.3.txt
        :language: text

    Reading the result: In this illustration, as_of excludes the 2025 revision. all keeps both earlier versions, whereas latest keeps only the newer visible version.

    :download:`Download the full example <../../../../example/2_financials.py>`

.. py:function:: get_factor(order_book_ids, factors, start_quarter, end_quarter, as_of=None)

    Quarterly derived financial factors.

    :param order_book_ids: One code or a list
    :param factors: Factor names; the available set comes from the server
    :param start_quarter: First quarter, like ``"2024q1"``
    :param end_quarter: Last quarter
    :param as_of: As for :py:func:`get_pit_financials_ex`
    :returns: ``DataFrame`` indexed by ``(order_book_id, quarter)``

    US codes are not supported, and the resulting error does not say so clearly —
    see :doc:`../howto/us_market`.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/2_financials.py
        :language: python
        :start-after: # [get_factor.1]
        :end-before: # [/get_factor.1]
        :prepend: from libfinance import get_factor

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_factor.1.txt
        :language: text

    .. literalinclude:: ../../../../example/2_financials.py
        :language: python
        :start-after: # [get_factor.2]
        :end-before: # [/get_factor.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_factor.2.txt
        :language: text

    Reading the result: Historical factor comparisons need the same as_of cutoff because later restatements can change calculated factors.

    :download:`Download the full example <../../../../example/2_financials.py>`
