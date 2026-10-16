==============
Share capital
==============

.. currentmodule:: libfinance

Security-code queries infer the market on the server and accept no market argument. Unsupported markets raise an error.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_shares`
      - Read historical share capital
    * - :func:`~libfinance.get_turnover_rate`
      - Read the daily turnover rate

Columns and units are covered in :doc:`../data/fundamentals`.

.. py:function:: get_shares(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None)

    Per-session share capital panel.

    :param order_book_ids: One code or a list
    :param start_date: Start date; omit to begin at the first share event
    :param end_date: End date; omit to run to the last event
    :param fields: Which columns; omit for all
    :returns: ``DataFrame`` indexed by ``(order_book_id, date)``
    :raises ValueError: for an unknown field name or an inverted date range

    Columns: ``total``, ``total_a``, ``circulation_a``, ``non_circulation_a``,
    ``free_circulation``, ``preferred_shares``. **All are counts of shares.**

    A-shares only; US codes raise "namespace 'shares' has no provider for
    market='us'".

    **Examples**

    .. lf-examples:: get_shares

    Reading the result: every value is in shares. A one-day query keeps both index levels; tradable shares (``tradable_shares``) and free float (``free_float_shares``) are different measures.

.. py:function:: get_turnover_rate(order_book_ids, start_date=None, end_date=None)

    Daily turnover rate for CN A shares and US stocks. The denominator is the A-share free float
    effective that day (tradable shares when free float is unavailable), or US shares outstanding on
    that date. The numerator is unadjusted volume. **A fraction**: 0.0123 is 1.23%.

    :param order_book_ids: One code or a list
    :param start_date: Start date; given alone, that day
    :param end_date: End date; with neither, each venue's latest trading day with bars in the last two weeks
    :returns: ``DataFrame`` indexed by ``(order_book_id, date)`` with one column, ``turnover_rate``
    :raises ValueError: for an inverted date range

    A suspended session has no row; a security or day without share data is NaN. The numbers are the
    CN values are the turnover the factors of factors-daybar read (``system/broker-daybar/TURN20``,
    ``system/barra-cne5-descriptor/STOM`` ...).

    .. code-block:: python

        import libfinance as lf

        lf.get_turnover_rate(["600000.XSHG", "AAPL.US"], "2026-09-01", "2026-09-30")
        lf.get_turnover_rate(["600000.XSHG", "AAPL.US"])   # each venue's latest trading day
