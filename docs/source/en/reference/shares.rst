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

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/4a_shares.py
        :language: python
        :start-after: # [get_shares.1]
        :end-before: # [/get_shares.1]
        :prepend: from libfinance import get_shares

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_shares.1.txt
        :language: text

    .. literalinclude:: ../../../../example/4a_shares.py
        :language: python
        :start-after: # [get_shares.2]
        :end-before: # [/get_shares.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_shares.2.txt
        :language: text

    .. literalinclude:: ../../../../example/4a_shares.py
        :language: python
        :start-after: # [get_shares.3]
        :end-before: # [/get_shares.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_shares.3.txt
        :language: text

    Reading the result: All values are in shares. A single-day query retains both index levels; circulating A-shares and free float are different measures.

    :download:`Download the full example <../../../../example/4a_shares.py>`
