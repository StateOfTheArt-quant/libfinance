==============================
Security codes and master data
==============================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/instruments`.

.. py:function:: all_instruments(type=None, date=None, market=None, cached=True)

    Master data for every security.

    :param type: ``"CS"`` (stocks) or ``"INDX"`` (indices); the aliases
        ``"STOCK"`` and ``"INDEX"`` are accepted, and a list may be passed.
        Omit for everything.
    :param date: Snapshot as of this day (the server calls this ``as_of``).
        Omit for the latest.
    :param market: Market; omit for the server default.
    :param cached: Use the local cache. Master data changes slowly, so this
        defaults to on.
    :returns: ``DataFrame`` with ``order_book_id`` as the first column

    .. code-block:: python

        >>> all_instruments(type="CS").shape
        (10616, 6)
        >>> all_instruments(type="CS", market="us").shape
        (5395, 6)

.. py:function:: instruments(order_book_ids, date=None, market=None)

    Master data for specific securities.

    :param order_book_ids: One code or a list, e.g. ``"000001.XSHE"``
    :param date: Snapshot as of this day (the server calls this ``as_of``)
    :param market: Market; omit for the server default
    :returns: A single :py:class:`~libfinance.api.instrument.Instrument` for a single code (``None`` if not
        found), or a list of them for a list of codes. Codes that cannot be
        resolved are skipped, so the list may be shorter than the input.

    .. code-block:: python

        >>> instruments("600000.XSHG")
        Instrument(order_book_id='600000.XSHG', symbol='浦发银行', type='CS',
                   market='cn', listed_date='1999-11-10T00:00:00.000')

    Pass ``date`` to resolve securities that have since been delisted:

    .. code-block:: python

        >>> instruments("600837.XSHG")                        # today
        None
        >>> instruments("600837.XSHG", date="2022-09-20")     # as of 2022
        Instrument(order_book_id='600837.XSHG', symbol='海通证券', ...)

.. currentmodule:: libfinance.api.instrument

.. py:class:: Instrument

    Master data for one security. Attribute names match the ``DataFrame`` columns:
    ``order_book_id``, ``symbol``, ``type``, ``market``, ``listed_date``,
    ``de_listed_date``.

    ``order_book_id`` is the **code**; ``symbol`` is the **name**.
