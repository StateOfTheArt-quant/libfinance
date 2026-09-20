==============================
Stock universes: three lenses
==============================

"Pick a set of stocks" has three common definitions here, each with its own source
and update cadence:

.. list-table::
    :header-rows: 1
    :widths: 20 30 50

    *   - Lens
        - Function
        - Character
    *   - Index constituents
        - :func:`~libfinance.get_index_weights`
        - Weighted, transparent rules, periodic rebalancing
    *   - Industry
        - :func:`~libfinance.get_industry` / :func:`~libfinance.get_industry_mapping`
        - Full market coverage, three levels
    *   - Concept sectors
        - :func:`~libfinance.get_concept_weights`
        - Theme-driven, numerous, fuzzy boundaries

Index constituents and weights
==============================

.. code-block:: python

    >>> from libfinance import get_index_weights
    >>> get_index_weights(index_code="000300.XSHG", date="2024-03-08").head()
        index_code       date order_book_id   weight
    0  000300.XSHG 2024-03-08   000001.XSHE  0.00576
    1  000300.XSHG 2024-03-08   000002.XSHE  0.00383
    2  000300.XSHG 2024-03-08   000063.XSHE  0.00534
    3  000300.XSHG 2024-03-08   000069.XSHE  0.00085
    4  000300.XSHG 2024-03-08   000100.XSHE  0.00477

Weights are normalised:

.. code-block:: python

    >>> get_index_weights(index_code="000300.XSHG", date="2024-03-08")["weight"].sum()
    0.9999999996000001

.. note::

    **Any trading day works, not just rebalancing dates.**

    Index providers publish weights only on rebalancing dates. Weights for other
    days are derived: take the most recent published snapshot at or before the
    date, re-weight each constituent by its **adjusted** return from that snapshot
    to the target date, then normalise.

    Using adjusted returns is essential — with a bonus issue or split inside the
    window, raw price changes would misread a share-count change as a return.

Omit ``date`` for the latest snapshot. The argument is ``index_code`` (not
``index_id``).

The result has four columns and carries no index or constituent names — names are
security master data; fetch them with :func:`~libfinance.instruments` if needed.

Industry classification
=======================

Currently Shenwan only (``source="sw"``), in three levels:

.. code-block:: python

    >>> from libfinance import get_industry_mapping
    >>> get_industry_mapping().shape
    (346, 6)
    >>> get_industry_mapping().head(3)
      first_industry_code first_industry_name second_industry_code second_industry_name  \
    0              110000                农林牧渔               110100                  种植业
    1              110000                农林牧渔               110100                  种植业
    2              110000                农林牧渔               110100                  种植业

      third_industry_code third_industry_name
    0              110101                  种子
    1              110102                粮食种植
    2              110103               其他种植业

This is the **classification tree** — one row per third-level industry.

To look up which industry a stock belongs to:

.. code-block:: python

    >>> from libfinance import get_instrument_industry
    >>> get_instrument_industry(["000001.XSHE", "600000.XSHG"], date="2024-03-08")
                  first_industry_code first_industry_name
    order_book_id
    000001.XSHE                480000                  银行
    600000.XSHG                480000                  银行

``level`` selects the depth (1/2/3, default 1).

To go the other way and list an industry's members:

.. code-block:: python

    >>> from libfinance import get_industry
    >>> get_industry("480000")[:6]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE',
     '002839.XSHE', '002936.XSHE']

.. important::

    Industry membership changes. Historical backtests must pass ``date``, or you
    are slicing the past with **today's** classification — another form of
    look-ahead bias.

Concept sectors
===============

Currently one source only, THS (``source="THS"``). First list the concepts:

.. code-block:: python

    >>> from libfinance import get_concept_meta
    >>> get_concept_meta(source="THS").head(3)
      source concept_id concept_name established_date  component_number
    0    THS     300008        新能源汽车              NaN               NaN
    1    THS     300013          大飞机              NaN               NaN
    2    THS     300018         参股保险              NaN               NaN

Then fetch members by ``concept_id``:

.. code-block:: python

    >>> from libfinance import get_concept_weights
    >>> get_concept_weights(concept_ids=["300008"], source="THS").head(3)
      source concept_id       date order_book_id    weight
    0    THS     300008 2026-09-15   000009.XSHE  0.000943
    1    THS     300008 2026-09-15   000021.XSHE  0.000943
    2    THS     300008 2026-09-15   000062.XSHE  0.000943

.. warning::

    **Concept ids must come from :func:`~libfinance.get_concept_meta`.** An
    unknown id returns an empty table — and from the caller's side, "this concept
    has no members today" and "this id does not exist" look identical. The client
    warns about it:

    .. code-block:: python

        >>> get_concept_weights(concept_ids=["886074"], source="THS")
        UserWarning: 未知的 concept_id: 886074（source='THS'）...
        Empty DataFrame

    Do not hard-code concept ids; look them up from the metadata table.

``as_of`` applies here too: use the membership **known** at that point. Pass it
when building historical universes, for the reasons in :doc:`point_in_time`.
