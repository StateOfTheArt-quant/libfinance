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
    :param adjust_orig: Basis date of forward adjustment; defaults to ``end_date``: prices are expressed as of
        the window's last day, so ex-dates after the window do not change them (point-in-time)
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

    .. lf-examples:: get_price

    Reading the result: forward adjustment is based on the window's last day by default (``adjust_orig``), so ex-dates after the window leave it unchanged -- here it equals the raw price; backward adjustment is based on the first listing day, scaling prices up and volume down by the same ratio.

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

    .. lf-examples:: get_price_coverage

    Reading the result: coverage is given by security type and exchange; the second example counts 5 trading days back from the stocks' (XSHE) ``end``, so the window moves with the data version.

