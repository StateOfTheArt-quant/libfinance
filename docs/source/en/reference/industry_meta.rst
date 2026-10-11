===================
Industry code table
===================

Every node of every industry classification. The table is generated from the service by
``docs/_shared/generate_catalogs.py`` and reflects the classification **on the day it was generated**.
Classifications get revised (Shenwan had 400 nodes before its 2021 revision and 608 after); query a past
classification with ``as_of``:

.. code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="industry", source="SW")                      # Shenwan today
    >>> lf.all_instruments(type="industry", source="SW", as_of="2020-01-02")  # before the revision
    >>> lf.instruments("480301.SW")                                           # level and parent

What an industry classification is and how the systems differ: :doc:`../concepts/classification`.

Columns
=======

.. list-table::
    :header-rows: 1
    :widths: 18 30 52

    * - Column
      - Field
      - Meaning
    * - Code
      - ``order_book_id``
      - Industry code, written ``<code>.<system>``; pass it to :func:`~libfinance.get_industry_constituents`
    * - Name
      - ``name``
      - Industry name, indented by level, so the table reads top-down as a tree
    * - Level
      - ``level``
      - ``1`` is the coarsest; the same as the ``level`` argument of :func:`~libfinance.get_instrument_industry`
    * - Parent
      - ``parent_order_book_id``
      - The node one level up; empty at level 1

The systems
===========

.. list-table::
    :header-rows: 1
    :widths: 12 10 28 50

    * - System
      - Market
      - Levels
      - Notes
    * - ``SW``
      - CN
      - 3: level 1 / 2 / 3
      - Shenwan Hongyuan Research, the standard for A-share research; the 2021 edition has 31 level-1
        industries, which are Barra CNE5's 31 industry factors
    * - ``GICS``
      - US
      - 4: Sector / Industry Group / Industry / Sub-Industry
      - Global Industry Classification Standard by MSCI and S&P Dow Jones Indices; the institutional standard
    * - ``ICB``
      - US
      - 4: Industry / Supersector / Sector / Subsector
      - Industry Classification Benchmark by FTSE Russell
    * - ``NAICS``
      - US
      - 5 (2- to 6-digit codes)
      - North American Industry Classification System; a statistical classification by production activity
    * - ``SIC``
      - US
      - 4: Division (letter) / Major Group / Industry Group / Industry
      - Standard Industrial Classification; older, still used in SEC filings

Shenwan (SW)
============

Nodes named "—" are nodes the service's current catalogue has no name for (mostly pre-2021 codes); the
codes themselves can still be queried.

.. csv-table::
    :file: ../../../_shared/tables/catalog_industry_sw.csv
    :header: Code, Name, Level, Parent
    :widths: 20, 50, 10, 20

GICS
====

.. csv-table::
    :file: ../../../_shared/tables/catalog_industry_gics.csv
    :header: Code, Name, Level, Parent
    :widths: 20, 50, 10, 20

ICB
===

.. dropdown:: Show all ICB nodes
    :icon: list-unordered

    .. csv-table::
        :file: ../../../_shared/tables/catalog_industry_icb.csv
        :header: Code, Name, Level, Parent
        :widths: 20, 50, 10, 20

NAICS
=====

.. dropdown:: Show all NAICS nodes (about 1,400)
    :icon: list-unordered

    .. csv-table::
        :file: ../../../_shared/tables/catalog_industry_naics.csv
        :header: Code, Name, Level, Parent
        :widths: 20, 50, 10, 20

SIC
===

.. dropdown:: Show all SIC nodes
    :icon: list-unordered

    .. csv-table::
        :file: ../../../_shared/tables/catalog_industry_sic.csv
        :header: Code, Name, Level, Parent
        :widths: 20, 50, 10, 20
