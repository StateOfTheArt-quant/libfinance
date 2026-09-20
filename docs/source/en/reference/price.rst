===========
Daily bars
===========

.. currentmodule:: libfinance

Security-code queries infer the market on the server and accept no market argument. Unsupported markets raise an error.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_price`
      - Read daily bars with field and adjustment choices
    * - :func:`~libfinance.get_price_coverage`
      - Find the last covered price date


Semantics are covered in :doc:`../data/price`; coverage bounds in
:doc:`../data/freshness`.

.. py:function:: get_price(order_book_ids, start_date, end_date, frequency='1d', fields=None, skip_suspended=False, include_now=True, adjust_type='pre', adjust_orig=None)

    Historical daily bars.

    :param order_book_ids: List of codes; required
    :param start_date: Start date; required
    :param end_date: End date; required
    :param frequency: Only ``"1d"`` is currently supported
    :param fields: Which columns to return; omit for all
    :param skip_suspended: Drop suspended days (zero volume). Default ``False``
    :param include_now: **No effect** on daily data; retained for signature
        compatibility
    :param adjust_type: ``"pre"`` (default, forward-adjusted), ``"none"``
        (unadjusted) or ``"post"`` (back-adjusted)
    :param adjust_orig: Basis date for adjustment; defaults to the release cutoff
    :returns: ``DataFrame`` indexed by ``(order_book_id, datetime)``
    :raises ValueError: for an unsupported ``frequency`` or ``adjust_type``
    :raises RpcError: if the range exceeds coverage, or back-adjustment spans an
        unpriceable corporate action

    .. danger::

        ``adjust_type`` defaults to ``"pre"``, so **the prices are not the prices
        that traded**. Pass ``adjust_type="none"`` for traded prices. This default
        changed in 0.0.2.

    Columns: ``open``, ``high``, ``low``, ``close``, ``volume``, ``turnover``,
    ``limit_up``, ``limit_down``. Volume is adjusted along with prices; turnover is
    not.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price.1]
        :end-before: # [/get_price.1]
        :prepend: from libfinance import get_price

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price.1.txt
        :language: text

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price.2]
        :end-before: # [/get_price.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price.2.txt
        :language: text

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price.3]
        :end-before: # [/get_price.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price.3.txt
        :language: text

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price.4]
        :end-before: # [/get_price.4]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price.4.txt
        :language: text

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price.5]
        :end-before: # [/get_price.5]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price.5.txt
        :language: text

    Reading the result: Adjustment changes prices and volume in opposite directions, while turnover stays the same. unstack turns each security into a column.

    :download:`Download the full example <../../../../example/1_get_price.py>`

.. py:function:: get_price_coverage(market='cn')

    How far daily price data reaches.

    :param market: ``"cn"`` (default) or ``"us"``
    :returns: ``{mic: {"start", "end", "raw_end", "adjust_cutoff"}}``
    :raises RuntimeError: if the server returns no usable coverage information.
        It does **not** return an empty dict, which would make "no coverage
        information" indistinguishable from "this market has no prices".

    ``end`` is the last date available for **adjusted** prices and is already the
    minimum of ``raw_end`` and ``adjust_cutoff``, so it is safe to use directly as
    ``end_date``.

    ``market`` has a default because the server binds both CN and US: without it
    the call raises ``AmbiguousMarketError`` rather than merging the two.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price_coverage.1]
        :end-before: # [/get_price_coverage.1]
        :prepend: from libfinance import get_price_coverage, get_price, get_n_trading_dates_until

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price_coverage.1.txt
        :language: text

    .. literalinclude:: ../../../../example/1_get_price.py
        :language: python
        :start-after: # [get_price_coverage.2]
        :end-before: # [/get_price_coverage.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_price_coverage.2.txt
        :language: text

    Reading the result: The second block reuses coverage from the first. The illustrated end date determines the trailing window; your version can have a different end date.

    :download:`Download the full example <../../../../example/1_get_price.py>`
