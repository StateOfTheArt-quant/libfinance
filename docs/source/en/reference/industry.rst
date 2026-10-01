=======================
Industry classification
=======================

.. currentmodule:: libfinance

An industry is named by an ``order_book_id`` (``<classification code>.<classification>``, e.g. ``480000.SW``,
``10.GICS``), with the same rules as a security; ``source`` is the classification (``SW``, ``GICS``, ...) and
``level`` its depth. All three functions answer with the facts of ``as_of``; a historical universe should
use one ``as_of`` for industry membership, constituents and weights.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_instrument_industry`
      - Map securities to their industries at a date
    * - :func:`~libfinance.get_industry_constituents`
      - Find the securities in an industry at a date
    * - :func:`~libfinance.get_industry_weights`
      - Read an industry's constituent weights, with their methodology


Semantics are covered in :doc:`../data/universe`.

.. py:function:: get_instrument_industry(order_book_ids, source=None, level=None, as_of=None)

    Which industries each security belongs to.

    :param order_book_ids: Security codes (one code is fine); each code names its market
    :param source: Classification, e.g. ``"SW"`` (Shenwan) or ``"GICS"``; omit for every classification
    :param level: Depth (Shenwan 1/2/3); omit for every level
    :param as_of: The facts of that day; omit for the latest confirmed date.
        **Pass this for historical work** — memberships change.
    :returns: ``DataFrame`` with ``order_book_id``, ``related_order_book_id`` (the industry code, e.g.
        ``480000.SW``), ``source``, ``market`` and ``level``

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/python/08_industry.py
        :language: python
        :start-after: # [get_instrument_industry.1]
        :end-before: # [/get_instrument_industry.1]
        :prepend: from libfinance import get_instrument_industry

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_instrument_industry.1.txt
        :language: text

    Reading the result: The loop prints level 1 and then level 3. ``related_order_book_id`` is the industry
    code and can be passed straight to :func:`~libfinance.get_industry_constituents`.

    :download:`Download the full example <../../../../example/python/08_industry.py>`

.. py:function:: get_industry_constituents(order_book_id, as_of=None)

    Every security in an industry on a day.

    :param order_book_id: Industry code, e.g. ``"480000.SW"`` (Shenwan banks) or ``"10.GICS"``
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: List of member ``order_book_id``; ``None`` when the industry did not exist that day

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/python/08_industry.py
        :language: python
        :start-after: # [get_industry_constituents.1]
        :end-before: # [/get_industry_constituents.1]
        :prepend: from libfinance import get_industry_constituents, get_instrument_industry

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_industry_constituents.1.txt
        :language: text

    Reading the result: The two lists illustrate historical and current membership. Placeholder codes show the structure only.

    :download:`Download the full example <../../../../example/python/08_industry.py>`

.. py:function:: get_industry_weights(order_book_id, as_of=None)

    The weights of an industry's constituents on a day.

    :param order_book_id: Industry code, e.g. ``"480000.SW"``
    :param as_of: The facts of that day; omit for the latest confirmed date
    :returns: ``DataFrame`` with ``order_book_id`` (the member), ``weight``, ``methodology``, ``source``,
        ``effective_from`` and ``effective_to``. No weights are made up: without a vendor weight and an
        explicit methodology there is no row.

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/python/08_industry.py
        :language: python
        :start-after: # [get_industry_weights.1]
        :end-before: # [/get_industry_weights.1]
        :prepend: from libfinance import get_industry_weights

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_industry_weights.1.txt
        :language: text

    Reading the result: One row per member; ``methodology`` says where the weight comes from.

    :download:`Download the full example <../../../../example/python/08_industry.py>`
