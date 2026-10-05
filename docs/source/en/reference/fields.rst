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

From :py:func:`~libfinance.all_instruments` and
:py:func:`~libfinance.instruments`:

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``order_book_id``
        - Security code, e.g. ``600000.XSHG``
    *   - ``symbol``
        - Security name
    *   - ``type``
        - ``CS`` stock / ``INDX`` index
    *   - ``market``
        - ``cn`` / ``us``
    *   - ``listed_date``
        - Listing date
    *   - ``de_listed_date``
        - Delisting date; ``NaN`` while still trading

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

Index and concept weights
=========================

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Column
        - Meaning
    *   - ``index_code`` / ``concept_id``
        - Index code / concept id
    *   - ``date``
        - The day the weights apply to
    *   - ``order_book_id``
        - Constituent code
    *   - ``weight``
        - Weight; sums to 1 within a day

Live quotes
===========

``Quote`` fields are listed in :doc:`../data/realtime`.
