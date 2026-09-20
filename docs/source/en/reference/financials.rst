===============
Financial data
===============

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/fundamentals`; ``as_of`` in
:doc:`../data/point_in_time`.

.. py:function:: get_pit_financials_ex(order_book_ids, fields, start_quarter, end_quarter, as_of=None, statements='latest', market=None)

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
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` indexed by ``(order_book_id, quarter)``, with
        ``info_date`` and ``if_adjusted`` alongside the requested fields

    .. code-block:: python

        >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4",
        ...                       as_of="2024-06-30")["net_profit"]
        -2.635887e+09
        >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4")["net_profit"]
        -2.730376e+09      # restated in 2026

.. py:function:: get_factor(order_book_ids, factors, start_quarter, end_quarter, as_of=None, market=None)

    Quarterly derived financial factors.

    :param order_book_ids: One code or a list
    :param factors: Factor names; the available set comes from the server
    :param start_quarter: First quarter, like ``"2024q1"``
    :param end_quarter: Last quarter
    :param as_of: As for :py:func:`get_pit_financials_ex`
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` indexed by ``(order_book_id, quarter)``

    US codes are not supported, and the resulting error does not say so clearly —
    see :doc:`../howto/us_market`.
