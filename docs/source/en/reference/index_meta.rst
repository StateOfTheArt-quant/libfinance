================
Index code table
================

Codes, names and base information for every index. The table is generated from the service by
``docs/_shared/generate_catalogs.py`` and reflects the catalogue **on the day it was generated**; the
service you connect to may be newer, so trust the query:

.. code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="index")              # catalogue: code, name, market, publisher
    >>> lf.instruments("000300.XSHG")                 # one index: base date, base value, launch date
    >>> lf.all_instruments(type="index", as_of="2016-01-04")   # the catalogue on that day

What an index is and how to use one: :doc:`../concepts/classification`.

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
      - Index code; pass it straight to :func:`~libfinance.get_price` or :func:`~libfinance.get_index_constituents`
    * - Publisher
      - ``source``
      - Who compiles and publishes the index: ``CSI`` China Securities Index, ``CNI`` China National Index,
        ``SZSE`` Shenzhen Stock Exchange, ``SPDJI`` S&P Dow Jones Indices, ``NASDAQ``, ``FTSE_RUSSELL``;
        blank when the catalogue records no publisher
    * - Base date / value
      - ``base_date`` / ``base_value``
      - The day and level the index starts from. Levels are comparable only within one index
    * - Launch date
      - ``established_date``
      - When the index was officially published. **Levels before the launch date are back-calculated**:
        nobody knew the index would exist
    * - Members
      - ``len(get_index_constituents(...))``
      - Number of constituents in the latest period; blank when the service has no constituent data for
        the index, only its level

Indices with constituent data
=============================

Only these indices can serve as a **benchmark** or a **historical universe** (constituents and weights
answer with the facts of ``as_of``).

.. csv-table::
    :file: ../../../_shared/tables/catalog_index_constituents.csv
    :header: Code, Name, Market, Publisher, Base date, Base value, Launch date, Members
    :widths: 14, 22, 6, 12, 12, 8, 12, 8

All indices
===========

.. dropdown:: Show all indices (about 1,000)
    :icon: list-unordered

    .. csv-table::
        :file: ../../../_shared/tables/catalog_index.csv
        :header: Code, Name, Market, Publisher, Base date, Base value, Launch date, Members
        :widths: 14, 22, 6, 12, 12, 8, 12, 8
