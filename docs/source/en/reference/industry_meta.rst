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

What an industry classification is and how the systems differ: :doc:`../tutorials/classification`.

How to read it
==============

Each system is a tree with only level 1 shown; click a row to open the level below it, or use ``+`` / ``−`` at
the top right to open or close everything. On each row the left is the industry code (``order_book_id``,
written ``<code>.<system>``, which you can pass to :func:`~libfinance.get_industry_constituents`), the middle
is the name, and the number on the right counts the nodes one level down. Indentation depth is the level
(``level``, ``1`` the coarsest), the same as the ``level`` argument of :func:`~libfinance.get_instrument_industry`.

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

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_sw.html

GICS
====

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_gics.html

ICB
===

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_icb.html

NAICS
=====

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_naics.html

SIC
===

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_sic.html
