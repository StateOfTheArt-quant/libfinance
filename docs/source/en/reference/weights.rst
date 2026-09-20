================================
Index and concept constituents
================================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/universe`.

Indices
=======

.. py:function:: get_index_weights(index_code, date=None, market=None)

    Index constituents and weights on **any trading day**.

    :param index_code: Index code, e.g. ``"000300.XSHG"``. The old argument name
        ``index_id`` was renamed — the server rejects it as unknown.
    :param date: The day; omit for the latest published snapshot
    :param market: Market; ``"cn"`` by default
    :returns: ``DataFrame`` with ``index_code``, ``date``, ``order_book_id``,
        ``weight``

    Providers publish weights only on rebalancing dates. Weights for other days are
    derived from the most recent snapshot, re-weighted by each constituent's
    **adjusted** return to the target date, then normalised.

    .. code-block:: python

        >>> get_index_weights(index_code="000300.XSHG", date="2024-03-08")["weight"].sum()
        0.9999999996000001

    The result carries no index or constituent names — fetch those from
    :py:func:`instruments`.

Concept sectors
===============

.. py:function:: get_concept_meta(source='THS', fields=None, market=None)

    Every concept sector in a source.

    :param source: Only ``"THS"`` is currently supported
    :param fields: Which columns; omit for all
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` with ``source``, ``concept_id``, ``concept_name`` and more

.. py:function:: get_concept_weights(concept_ids, as_of=None, source='THS', market=None)

    Constituents and weights of a concept sector.

    :param concept_ids: List of concept ids, taken from
        :py:func:`get_concept_meta`
    :param as_of: Use the membership **known** at that point; omit for the latest.
        The old name ``date`` still works but emits a ``DeprecationWarning``.
    :param source: Only ``"THS"`` is currently supported
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` with ``source``, ``concept_id``, ``date``,
        ``order_book_id``, ``weight``

    An unknown ``concept_id`` returns an empty table with a warning — from the
    caller's side, "no members today" and "no such id" look identical, so the
    client checks against the metadata table.
