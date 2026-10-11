================================
Theme (concept) code table
================================

Tonghuashun (THS) themes, the "concept boards" of the A-share market. The table is generated from the
service by ``docs/_shared/generate_catalogs.py`` and reflects the catalogue **on the day it was
generated**:

.. code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="theme")                  # catalogue
    >>> lf.get_theme_constituents("300008.THS")           # one theme's members
    >>> lf.get_instrument_themes("600000.XSHG")           # the themes a stock belongs to

.. warning::

    Theme history is short: theme data starts on the day in the "Effective from" column, and an earlier
    ``as_of`` raises ``CoverageError``. Backtesting the past with today's theme lists carries future
    information in the lists themselves (many themes are created, and their members confirmed, after the
    fact). See :doc:`../concepts/classification`.

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
      - Theme code, written ``<number>.THS``
    * - Name
      - ``name``
      - Theme name
    * - Members
      - ``len(get_theme_constituents(...))``
      - Number of member stocks in the latest period. One stock can belong to many themes
    * - Effective from
      - ``effective_from``
      - When the current member list took effect; also the earliest date you can query

All themes
==========

.. csv-table::
    :file: ../../../_shared/tables/catalog_theme_ths.csv
    :header: Code, Name, Members, Effective from
    :widths: 20, 40, 15, 25
