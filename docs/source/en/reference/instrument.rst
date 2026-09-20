==============================
Security codes and master data
==============================

.. currentmodule:: libfinance

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.all_instruments`
      - List securities by market, type and historical date
    * - :func:`~libfinance.instruments`
      - Resolve one or more codes, including mixed markets


Semantics are covered in :doc:`../data/instruments`.

.. py:function:: all_instruments(type=None, date=None, market=None, cached=True)

    Master data for every security.

    :param type: ``"CS"`` (stocks) or ``"INDX"`` (indices); the aliases
        ``"STOCK"`` and ``"INDEX"`` are accepted, and a list may be passed.
        Omit for everything.
    :param date: Snapshot as of this day (the server calls this ``as_of``).
        Omit for the latest.
    :param market: Market; omit to combine all bound markets.
    :param cached: Use the data-version cache when market is omitted; explicit market queries bypass it.
    :returns: ``DataFrame`` with ``order_book_id`` as the first column

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [all_instruments.1]
        :end-before: # [/all_instruments.1]
        :prepend: from libfinance import all_instruments

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/all_instruments.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [all_instruments.2]
        :end-before: # [/all_instruments.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/all_instruments.2.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [all_instruments.3]
        :end-before: # [/all_instruments.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/all_instruments.3.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [all_instruments.4]
        :end-before: # [/all_instruments.4]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/all_instruments.4.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [all_instruments.5]
        :end-before: # [/all_instruments.5]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/all_instruments.5.txt
        :language: text

    Reading the result: The type and market filters change the universe; date selects an identity snapshot. A historical query may still contain the same securities.

    :download:`Download the full example <../../../../example/0a_instrument.py>`

.. py:function:: instruments(order_book_ids, date=None)

    Master data for specific securities. Codes from multiple markets may be mixed;
    no market parameter is needed.

    :param order_book_ids: One code or a list, e.g. ``"000001.XSHE"``
    :param date: Snapshot as of this day (the server calls this ``as_of``)
    :returns: A single :py:class:`~libfinance.api.instrument.Instrument` for a single code (``None`` if not
        found), or a list of them for a list of codes. Codes that cannot be
        resolved are skipped, so the list may be shorter than the input.

    Pass ``date`` to resolve securities that have since been delisted:

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [instruments.1]
        :end-before: # [/instruments.1]
        :prepend: from libfinance import instruments

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/instruments.1.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [instruments.2]
        :end-before: # [/instruments.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/instruments.2.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [instruments.3]
        :end-before: # [/instruments.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/instruments.3.txt
        :language: text

    .. literalinclude:: ../../../../example/0a_instrument.py
        :language: python
        :start-after: # [instruments.4]
        :end-before: # [/instruments.4]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/instruments.4.txt
        :language: text

    Reading the result: A string returns one object; a list returns objects in input order. Historical queries resolve the code valid at that date.

    :download:`Download the full example <../../../../example/0a_instrument.py>`

.. currentmodule:: libfinance.api.instrument

.. py:class:: Instrument

    Master data for one security. Attribute names match the ``DataFrame`` columns:
    ``order_book_id``, ``symbol``, ``type``, ``market``, ``listed_date``,
    ``de_listed_date``.

    ``order_book_id`` is the **code**; ``symbol`` is the **name**.
