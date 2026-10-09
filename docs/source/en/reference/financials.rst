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
    * - :func:`~libfinance.get_financial_metrics`
      - Read derived financial metrics on each trading day

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

    .. lf-examples:: get_pit_financials_ex

    Reading the result: without ``as_of``, 2024q1 is the 2025 restatement (``if_adjusted`` 1); with ``as_of="2024-11-01"`` each quarter is the latest version known then; ``statements="all"`` lists every version visible then -- 2024q2 has its August disclosure and its October revision.

.. py:function:: get_financial_metrics(order_book_ids, fields, start_date=None, end_date=None)

    Derived financial metrics, one formula set for CN and US. A
    trading day's value comes from the latest report visible after that day's close: values jump on
    announcement days and stay flat in between; one the latest report cannot give is NaN.

    :param order_book_ids: One code or a list
    :param fields: Metric names, e.g. ``roe_lf``, ``revenue_ttm``, ``net_profit_growth_lyr``, ``debt_to_assets_lf``
    :param start_date: First day; with ``end_date`` omitted as well, the latest trading day
    :param end_date: Last day
    :returns: ``DataFrame`` indexed by ``(order_book_id, date)``, one column per metric

    **Examples**

    .. lf-examples:: get_financial_metrics

