=======================
Industry classification
=======================

.. currentmodule:: libfinance

get_instrument_industry infers markets from security codes. Industry identifiers and catalogs still accept market.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_industry_mapping`
      - Discover industry codes and hierarchy
    * - :func:`~libfinance.get_instrument_industry`
      - Map securities to industries at a date
    * - :func:`~libfinance.get_industry`
      - Find securities belonging to an industry


Semantics are covered in :doc:`../data/universe`. Only Shenwan (``source="sw"``) is
currently supported.

.. py:function:: get_industry_mapping(source='sw', date=None, market=None)

    The whole classification tree — codes, names, levels.

    :param source: Classification source; defaults to ``"sw"`` (Shenwan)
    :param date: Use the classification as of this day; omit for the latest
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` with one row per third-level industry

    Columns: ``first_industry_code`` / ``first_industry_name`` and the same for
    ``second_`` and ``third_``.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/3a_industry.py
        :language: python
        :start-after: # [get_industry_mapping.1]
        :end-before: # [/get_industry_mapping.1]
        :prepend: from libfinance import get_industry_mapping

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_industry_mapping.1.txt
        :language: text

    .. literalinclude:: ../../../../example/3a_industry.py
        :language: python
        :start-after: # [get_industry_mapping.2]
        :end-before: # [/get_industry_mapping.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_industry_mapping.2.txt
        :language: text

    Reading the result: Historical and current classifications can be identical or differ following classification changes.

    :download:`Download the full example <../../../../example/3a_industry.py>`

.. py:function:: get_instrument_industry(order_book_ids, date=None, source='sw', level=1)

    Which industry each security belongs to.

    :param order_book_ids: List of stock codes
    :param date: Use the classification as of this day; omit for the latest.
        **Pass this for historical work** — memberships change.
    :param source: Classification source; only ``"sw"`` is supported
    :param level: Depth, 1/2/3; default 1
    :returns: ``DataFrame`` indexed by ``order_book_id``

    The default ``source`` was ``"010303"`` before 0.0.6, which the server never
    accepted — calls with default arguments always failed.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/3a_industry.py
        :language: python
        :start-after: # [get_instrument_industry.1]
        :end-before: # [/get_instrument_industry.1]
        :prepend: from libfinance import get_instrument_industry

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_instrument_industry.1.txt
        :language: text

    Reading the result: The loop prints level 1 and then level 3. Code and name fields change with the chosen level; other columns are omitted.

    :download:`Download the full example <../../../../example/3a_industry.py>`

.. py:function:: get_industry(industry, source='sw', date=None, market=None)

    Every security in an industry.

    :param industry: Industry code or name
    :param source: Classification source; defaults to ``"sw"``
    :param date: Use the classification as of this day; omit for the latest
    :param market: Market; omit for the server default
    :returns: List of codes

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/3a_industry.py
        :language: python
        :start-after: # [get_industry.1]
        :end-before: # [/get_industry.1]
        :prepend: from libfinance import get_industry, get_industry_mapping

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_industry.1.txt
        :language: text

    Reading the result: The two lists illustrate historical and current membership. Placeholder codes show the structure only.

    :download:`Download the full example <../../../../example/3a_industry.py>`
