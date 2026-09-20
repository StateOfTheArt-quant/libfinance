==============
Share capital
==============

.. currentmodule:: libfinance

Columns and units are covered in :doc:`../data/fundamentals`.

.. py:function:: get_shares(order_book_ids, start_date=None, end_date=None, fields=None)

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
