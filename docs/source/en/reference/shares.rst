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

