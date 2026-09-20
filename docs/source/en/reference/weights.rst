================================
Index and concept constituents
================================

.. currentmodule:: libfinance

get_index_weights infers the market from the complete index code. Concept IDs are not security codes; concept queries still accept market.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_index_weights`
      - Read index constituents and weights at a trading date
    * - :func:`~libfinance.get_concept_meta`
      - Discover concept names and identifiers
    * - :func:`~libfinance.get_concept_weights`
      - Read concept constituents as known at a cutoff


Semantics are covered in :doc:`../data/universe`.

Indices
=======

.. py:function:: get_index_weights(index_code, date=None)

    Index constituents and weights on **any trading day**.

    :param index_code: Index code, e.g. ``"000300.XSHG"``. The old argument name
        ``index_id`` was renamed — the server rejects it as unknown.
    :param date: The day; omit for the latest published snapshot
    :returns: ``DataFrame`` with ``index_code``, ``date``, ``order_book_id``,
        ``weight``

    Providers publish weights only on rebalancing dates. Weights for other days are
    derived from the most recent snapshot, re-weighted by each constituent's
    **adjusted** return to the target date, then normalised.

    The result carries no index or constituent names — fetch those from
    :py:func:`instruments`.

Concept sectors
===============

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/index_component.py
        :language: python
        :start-after: # [get_index_weights.1]
        :end-before: # [/get_index_weights.1]
        :prepend: from libfinance import get_index_weights

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_index_weights.1.txt
        :language: text

    .. literalinclude:: ../../../../example/index_component.py
        :language: python
        :start-after: # [get_index_weights.2]
        :end-before: # [/get_index_weights.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_index_weights.2.txt
        :language: text

    .. literalinclude:: ../../../../example/index_component.py
        :language: python
        :start-after: # [get_index_weights.3]
        :end-before: # [/get_index_weights.3]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_index_weights.3.txt
        :language: text

    .. literalinclude:: ../../../../example/index_component.py
        :language: python
        :start-after: # [get_index_weights.4]
        :end-before: # [/get_index_weights.4]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_index_weights.4.txt
        :language: text

    Reading the result: Omitting date selects the latest anchor. The sum uses the complete result, not only the displayed rows.

    :download:`Download the full example <../../../../example/index_component.py>`

.. py:function:: get_concept_meta(source='THS', fields=None, market=None)

    Every concept sector in a source.

    :param source: Only ``"THS"`` is currently supported
    :param fields: Which columns; omit for all
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` with ``source``, ``concept_id``, ``concept_name`` and more

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/3b_concept_components.py
        :language: python
        :start-after: # [get_concept_meta.1]
        :end-before: # [/get_concept_meta.1]
        :prepend: from libfinance import get_concept_meta

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_concept_meta.1.txt
        :language: text

    .. literalinclude:: ../../../../example/3b_concept_components.py
        :language: python
        :start-after: # [get_concept_meta.2]
        :end-before: # [/get_concept_meta.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_concept_meta.2.txt
        :language: text

    Reading the result: DEMO01 and DEMO02 are illustrative identifiers, not queryable IDs. The script obtains real IDs from the catalog; fields limits the columns.

    :download:`Download the full example <../../../../example/3b_concept_components.py>`

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

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/3b_concept_components.py
        :language: python
        :start-after: # [get_concept_weights.1]
        :end-before: # [/get_concept_weights.1]
        :prepend: from libfinance import get_concept_weights, get_concept_meta

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_concept_weights.1.txt
        :language: text

    Reading the result: The three tables show one concept, two concepts, and historical visible membership. The second concept has no visible historical record in this illustration.

    :download:`Download the full example <../../../../example/3b_concept_components.py>`
