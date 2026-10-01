=================================
Index and theme constituents
=================================

.. currentmodule:: libfinance

Indices (``000300.XSHG``, ``SPX.US``) and themes (``300900.THS``) are named by an ``order_book_id``, with the
same rules as a security; their catalogues are ``all_instruments(type="index")`` and
``all_instruments(type="theme")``. Every function answers with the facts of ``as_of``.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_instrument_indices`
      - Map securities to the indices they belong to at a date
    * - :func:`~libfinance.get_index_constituents`
      - Find the securities in an index at a date
    * - :func:`~libfinance.get_index_weights`
      - Read an index's constituent weights, with their methodology
    * - :func:`~libfinance.get_instrument_themes`
      - Map securities to the themes they belong to at a date
    * - :func:`~libfinance.get_theme_constituents`
      - Find the securities in a theme at a date
    * - :func:`~libfinance.get_theme_weights`
      - Read a theme's constituent weights, with their methodology

Indices
=======

.. py:function:: get_instrument_indices(order_book_ids, source=None, as_of=None)

    :param order_book_ids: Security codes (one code is fine); each code names its market
    :param source: Index publisher, e.g. ``"CSI"`` or ``"SPDJI"``; omit for every publisher
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: ``DataFrame`` with ``order_book_id``, ``related_order_book_id`` (the index), ``source``,
        ``market`` and ``level``

.. py:function:: get_index_constituents(order_book_id, as_of=None)

    :param order_book_id: Index code, e.g. ``"000300.XSHG"``
    :param as_of: The facts of that day; omit for the index's latest confirmed date
    :returns: List of member ``order_book_id``; ``None`` when no market publishes the index

.. py:function:: get_index_weights(order_book_id, as_of=None)

    :param order_book_id: Index code, e.g. ``"000300.XSHG"``
    :param as_of: The facts of that day; omit for the index's latest confirmed date
    :returns: ``DataFrame`` with ``order_book_id`` (the member), ``weight``, ``methodology``, ``source``,
        ``effective_from`` and ``effective_to``

    :download:`Download the full example <../../../../example/python/09_index.py>`

Themes
======

.. py:function:: get_instrument_themes(order_book_ids, source=None, as_of=None)

    :param order_book_ids: Security codes (one code is fine); each code names its market
    :param source: Theme catalogue, e.g. ``"THS"``; omit for every catalogue
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: ``DataFrame`` with ``order_book_id``, ``related_order_book_id`` (the theme), ``source``,
        ``market`` and ``level``

.. py:function:: get_theme_constituents(order_book_id, as_of=None)

    :param order_book_id: Theme code, e.g. ``"300900.THS"``
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: List of member ``order_book_id``; ``None`` when the theme did not exist that day

.. py:function:: get_theme_weights(order_book_id, as_of=None)

    :param order_book_id: Theme code, e.g. ``"300900.THS"``
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: ``DataFrame`` with ``order_book_id`` (the member), ``weight``, ``methodology``, ``source``,
        ``effective_from`` and ``effective_to``. THS weights are ``derived_equal_weight``: equal weights
        derived from the member list, not vendor weights.

    :download:`Download the full example <../../../../example/python/10_theme.py>`
