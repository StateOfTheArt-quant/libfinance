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
      - List securities by type (stock, index, industry, theme), market, numbering body or historical snapshot
    * - :func:`~libfinance.instruments`
      - Resolve codes; one list may mix all four types and both markets

The catalog holds four types in one table. ``source`` is the body that numbers the codes: the exchange
for a stock, the publisher for an index, the classification for an industry (SW in China; GICS, ICB,
NAICS and SIC in the US) and the theme catalogue for a theme (THS). Stocks, indices and SW industries
have history; the US classifications and themes are current snapshots for now.

.. list-table::
    :header-rows: 1
    :widths: 15 35 50

    * - type
      - codes
      - source
    * - stock
      - ``000001.XSHE``, ``AAPL.US``
      - XSHG / XSHE / XBSE, XNAS / XNYS
    * - index
      - ``000300.XSHG``, ``SPX.US``
      - CSI / CNI, SPDJI / NASDAQ / FTSE_RUSSELL
    * - industry
      - ``480000.SW``, ``45.GICS``
      - SW, GICS / ICB / NAICS / SIC
    * - theme
      - ``300008.THS``
      - THS

Semantics are covered in :doc:`../data/instruments`.

.. py:function:: all_instruments(type=None, market=None, source=None, as_of=None, cached=True)

    The catalog: every security of the selected types.

    :param type: ``"stock"``, ``"index"``, ``"industry"`` or ``"theme"`` (case-insensitive), or a
        list of them. Omit for all four.
    :param market: ``"cn"`` or ``"us"``; omit for both.
    :param source: The numbering body (``"XSHG"``, ``"CSI"``, ``"SW"``, ``"GICS"``, ``"THS"`` ...),
        or a list of them. Omit for all.
    :param as_of: The catalog as of this day. Omit for each type's and source's current state. A day
        before a type's published coverage raises ``CoverageError`` naming the type; narrow ``type``
        or ``source``.
    :param cached: Use the data-version cache when market is omitted; explicit market queries bypass it.
    :returns: ``DataFrame`` with columns ``order_book_id, type, market, name, exchange, source``

    **Examples**

    .. lf-examples:: all_instruments

    Reading the result: every type has the same columns; ``type``, ``market`` and ``source`` only
    change the universe. ``as_of`` selects an identity snapshot -- SW had 400 industry nodes before its
    2021 revision and 608 after.

.. py:function:: instruments(order_book_ids, as_of=None, last_known=False)

    Resolve codes of any type. The type comes from the code itself, and codes of both markets may be
    mixed; no type or market parameter is needed.

    :param order_book_ids: One code or a list, e.g. ``"000001.XSHE"``, ``["000300.XSHG", "480000.SW"]``
    :param as_of: Resolve the code valid on this day; omit for each type's current state.
    :param last_known: When ``True``, a stock or index code that is no longer listed on ``as_of``
        resolves to its last listing (industry and theme nodes have no listing to fall back to).
    :returns: A single :py:class:`~libfinance.api.instrument.Instrument` for a single code (``None`` if not
        found), or a list of them in input order for a list of codes. Codes that cannot be resolved are
        skipped, so the list may be shorter than the input. A code two types claim on the same day
        raises ``AmbiguousInstrumentError``.

    **Examples**

    .. lf-examples:: instruments

    Reading the result: a string returns one object; a list returns objects in input order. Historical
    queries resolve the code valid on that day; an ``as_of`` before a type's published coverage raises
    ``CoverageError``.

.. currentmodule:: libfinance.api.instrument

.. py:class:: Instrument

    One security. Attribute names are the :func:`~libfinance.all_instruments` columns --
    ``order_book_id``, ``type``, ``market``, ``name``, ``exchange``, ``source`` -- plus
    the fields of its type (``listed_date`` for a stock, ``level`` for an industry node, ...).

    ``order_book_id`` is the **code**, and the only identifier the client sees; ``name`` is the
    **name**.
