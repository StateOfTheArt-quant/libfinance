================
Field dictionary
================

Meanings and units of the columns each function returns.

Prices
======

Columns from :py:func:`~libfinance.get_price`:

.. list-table::
    :header-rows: 1
    :widths: 24 16 60

    *   - Column
        - Unit
        - Meaning
    *   - ``open`` / ``high`` / ``low`` / ``close``
        - currency
        - Open, high, low, close. Affected by ``adjust_type``
    *   - ``volume``
        - shares
        - Volume. **Also affected by adjustment** (scaled inversely to price)
    *   - ``turnover``
        - currency
        - Turnover. Not affected by adjustment
    *   - ``limit_up`` / ``limit_down``
        - currency
        - Daily price limits. ``NaN`` for US equities

Indexed by ``(order_book_id, datetime)``.

Security master
===============

The catalogue returned by :py:func:`~libfinance.all_instruments`:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``order_book_id``
        - Code, e.g. ``600000.XSHG``, ``000300.XSHG``, ``480000.SW``, ``300008.THS``
    *   - ``permanent_id``
        - Permanent ID: codes get renamed and reused, the permanent ID does not; use it to join one
          security across time
    *   - ``type``
        - ``stock`` / ``index`` / ``industry`` / ``theme``
    *   - ``market``
        - ``CN`` / ``US``
    *   - ``name``
        - Name, e.g. ``浦发银行``, ``沪深300``, ``Information Technology``
    *   - ``exchange``
        - Listing exchange; stocks only
    *   - ``source``
        - Who issued the code: the exchange for a stock, the publisher for an index (``CSI``,
          ``SPDJI``, ...), the classification system for an industry (``SW``, ``GICS``, ...), ``THS`` for a theme

:py:func:`~libfinance.instruments` returns objects with more attributes, depending on the type; for
indices, industries and themes see `Indices, industries and themes`_ below.

Share capital
=============

From :py:func:`~libfinance.get_shares`. **Every column counts shares**:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``total``
        - Total shares
    *   - ``total_a``
        - Total A-shares
    *   - ``circulation_a``
        - Floating A-shares
    *   - ``non_circulation_a``
        - Non-floating A-shares
    *   - ``free_circulation``
        - Free-float shares
    *   - ``preferred_shares``
        - Preferred shares

Corporate actions
=================

Dividends (:py:func:`~libfinance.get_dividends`):

.. list-table::
    :header-rows: 1
    :widths: 30 70

    *   - Column
        - Meaning
    *   - ``ex_date``
        - Ex-date; the price gap happens here
    *   - ``record_date``
        - Record date
    *   - ``payable_date``
        - Payment date
    *   - ``declaration_date``
        - Announcement date
    *   - ``cash_per_share``
        - Cash per share
    *   - ``bonus_per_share``
        - Bonus shares per share
    *   - ``transfer_per_share``
        - Capitalisation shares per share
    *   - ``dist_kind`` / ``marker``
        - Distribution type and marker
    *   - ``currency``
        - Currency

Splits (:py:func:`~libfinance.get_splits`): ``ratio_from`` / ``ratio_to`` read as
"``ratio_from`` shares become ``ratio_to`` shares".

Spin-offs (:py:func:`~libfinance.get_spinoffs`, US only): ``valuation_price`` is an
estimate and must be read with ``valuation_basis`` and ``valuation_source``.

Financials
==========

Besides the fields you request, :py:func:`~libfinance.get_pit_financials_ex`
returns two columns:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``info_date``
        - When this version was published; always ``<= as_of``
    *   - ``if_adjusted``
        - ``0`` originally reported, ``1`` restated

Available field and factor names come from the server and vary by deployment.

Indices, industries and themes
==============================

The code tables are :doc:`index_meta`, :doc:`industry_meta` and :doc:`theme_meta`; how the three
differ is in :doc:`../concepts/classification`.

Object attributes
-----------------

:py:func:`~libfinance.instruments` returns, for an index:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Attribute
        - Meaning
    *   - ``source``
        - Publisher: ``CSI`` China Securities Index, ``CNI`` China National Index, ``SZSE`` Shenzhen Stock
          Exchange, ``SPDJI`` S&P Dow Jones Indices, ``NASDAQ``, ``FTSE_RUSSELL``
    *   - ``trading_code``
        - The code without its namespace, e.g. ``000300``
    *   - ``base_date`` / ``base_value``
        - The day and level the index starts from
    *   - ``established_date``
        - Launch date. Levels before it are back-calculated
    *   - ``terminated_date``
        - Discontinuation date; ``None`` while still published
    *   - ``return_variant``
        - ``price``: a price index (dividends not reinvested); ``unspecified``: not recorded
    *   - ``currency``
        - Currency; ``None`` when not recorded
    *   - ``lifecycle_status``
        - ``active``: still published; ``unknown``: not recorded

For an industry or a theme:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Attribute
        - Meaning
    *   - ``source``
        - The classification system for an industry (``SW``, ``GICS``, ``ICB``, ``NAICS``, ``SIC``), ``THS`` for a theme
    *   - ``source_raw_id``
        - The system's own number, e.g. ``480000``
    *   - ``level``
        - Level, ``1`` the coarsest; ``None`` for themes, which have no levels
    *   - ``parent_order_book_id``
        - The node one level up; ``None`` for level-1 industries and for themes
    *   - ``effective_from`` / ``effective_to``
        - When this node (this edition of the classification) is in effect; ``effective_to`` is ``None`` while current

Membership lookups
------------------

:py:func:`~libfinance.get_instrument_industry`, :py:func:`~libfinance.get_instrument_indices` and
:py:func:`~libfinance.get_instrument_themes` return the same table; each row says "this security belongs
to that object":

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``order_book_id``
        - The security you passed
    *   - ``related_order_book_id``
        - The industry / index / theme it belongs to; pass it to the matching ``get_*_constituents``
    *   - ``source``
        - Classification system / index publisher / ``THS``
    *   - ``market``
        - ``CN`` / ``US``
    *   - ``level``
        - Industry level; empty for indices and themes

A security has exactly **one row per level of one classification system** (industries are mutually
exclusive); it can have any number of index and theme rows.

Index weights
-------------

:py:func:`~libfinance.get_index_weights`:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``order_book_id`` / ``permanent_id``
        - The constituent
    *   - ``weight``
        - Weight; sums to 1 within a day
    *   - ``date``
        - The day the weights belong to: the month-end snapshot, or ``as_of`` when drifted from one
    *   - ``source``
        - Index publisher
    *   - ``basis``
        - Where the weights come from: ``origin``, published by the data source; ``reconstructed``, rebuilt
          from the index methodology. One period never mixes the two
    *   - ``methodology``
        - How the weights are computed; see below
    *   - ``quality_flags``
        - Known approximations, as a list; empty means none known. See below

Values of ``methodology``:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Value
        - Meaning
    *   - ``VENDOR_SNAPSHOT``
        - A weight snapshot published by the index company or a data vendor, used as is
    *   - ``FREE_FLOAT_CAP``
        - Reconstructed by free-float market cap
    *   - ``MODIFIED_CAP``
        - Market-cap weighted with a cap on single constituents (e.g. Nasdaq-100)
    *   - ``PRICE_WEIGHTED``
        - Price weighted (e.g. the Dow Jones Industrial Average)
    *   - ``FULL_CAP_PROXY``
        - Approximated by total market cap: the real index is free-float weighted, but without the float
          adjustment total shares stand in

Values of ``quality_flags``:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Value
        - Meaning
    *   - ``DRIFTED``
        - Not a snapshot day: drifted from the latest snapshot by each constituent's adjusted return (computed client side)
    *   - ``NO_IWF``
        - Cap weighted, but total shares replace the index company's investable weight factor (IWF)
    *   - ``SHARES_NOT_PIT``
        - When the share counts became known is unknown or later than the snapshot; they cannot be shown to
          have been known at the time
    *   - ``INCOMPLETE_MEMBERS``
        - Up to 5% of the period's constituents lack inputs; weights are computed over the rest
    *   - ``CAP_AT_ANCHOR``
        - Weight caps applied on the month-end snapshot rather than the index's actual rebalance day
    *   - ``STALE_PRICE``
        - No close on the snapshot day; the latest close within 7 days is used
    *   - ``DELISTED_BEFORE_SNAPSHOT``
        - The snapshot still holds a security delisted a few days earlier (the index company removes it at
          the next review)

Weights flagged ``NO_IWF`` or ``SHARES_NOT_PIT`` are fine as an approximate benchmark, not for tracking
that must replicate the index exactly.

Industry and theme weights
--------------------------

:py:func:`~libfinance.get_industry_weights` and :py:func:`~libfinance.get_theme_weights`:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``order_book_id``
        - The constituent
    *   - ``weight``
        - Weight; sums to 1
    *   - ``methodology``
        - ``derived_equal_weight``: equal weights derived from the member list. Classifications publish member
          lists, not weights; these are not vendor weights
    *   - ``source``
        - Classification system / ``THS``
    *   - ``effective_from`` / ``effective_to``
        - When this member list is in effect; ``effective_to`` is ``None`` while current

Live quotes
===========

``Quote`` fields are listed in :doc:`../data/realtime`.
