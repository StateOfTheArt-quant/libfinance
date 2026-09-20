===========
Daily bars
===========

.. currentmodule:: libfinance

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

    .. code-block:: python

        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")["close"]
        8.813035      # forward-adjusted
        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06",
        ...           adjust_type="none")["close"]
        10.49         # as traded

    Index codes return an **empty table** with no warning — this function serves
    stocks only.

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

    .. code-block:: python

        >>> get_price_coverage()
        {'XSHE': {'start': '2000-01-04', 'end': '2026-09-18',
                  'raw_end': '2026-09-18', 'adjust_cutoff': '2026-09-18'},
         'XSHG': {...}}

    ``market`` has a default because the server binds both CN and US: without it
    the call raises ``AmbiguousMarketError`` rather than merging the two.
