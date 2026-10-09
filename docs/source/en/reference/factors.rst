=========
7 Factors
=========

.. currentmodule:: libfinance

Daily factors come from factors-daybar: qlib and alpha158 price-volume factors, and the Barra CNE5
style, industry and country factors with their raw descriptors. Factor names are written **in full**:
a library ``owner/library[@rev]`` (all its factors) or a factor ``owner/library/factor[@rev]``, mixed
freely in one request; there are no short names. ``start_date == end_date`` is that day's cross section.

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_factor_exposure`
      - Read factor exposures for codes over a date range
    * - :func:`~libfinance.list_factor_libraries`
      - The factor libraries, their versions and factor counts
    * - :func:`~libfinance.list_factors`
      - The factors of one library

.. list-table::
    :header-rows: 1
    :widths: 28 72

    * - Library
      - Contents
    * - ``system/qlib``, ``system/alpha158``
      - qlib price-volume factors; alpha158 is qlib's Alpha158 set (158 factors referring to ``system/qlib``)
    * - ``system/barra-cne5``
      - 10 styles (SIZE, BETA, MOMENTUM, RESVOL, NLSIZE, BTOP, LIQUIDITY, EARNYILD, GROWTH, LEVERAGE), 31
        Shenwan level-1 industry dummies and COUNTRY. The styles are cross-sectionally standardized
        exposures (float-cap-weighted mean 0, equal-weighted std 1), computed when read over ``universe``
    * - ``system/barra-cne5-descriptor``, ``system/barra-cne6-descriptor``
      - Raw Barra descriptors (LNCAP, BETA, STOM, ...): each security's own time series, independent of any universe

**Free tier**: without login, ``get_factor_exposure`` pulls start_date up to one year before today and
takes at most 300 codes per call; the client warns when a request will be cut. No limit after login.

.. py:function:: get_factor_exposure(order_book_ids, factor_names, start_date, end_date, universe=None)

    Factor exposures.

    :param order_book_ids: One code or a list
    :param factor_names: Library names (``"system/barra-cne5"``) or full factor names
        (``"system/qlib/MA5"``), one or a list, mixed
    :param start_date: First day; equal to ``end_date`` for that day's cross section
    :param end_date: Last day
    :param universe: The codes cross-sectional factors are computed over; omitted, each day's A-share
        market. Time-series factors ignore it
    :returns: ``DataFrame`` indexed by ``(order_book_id, date)``, one float32 column per factor, named in
        full (a library expands to ``owner/library/factor``)

    **Examples**

    .. lf-examples:: get_factor_exposure

.. py:function:: list_factor_libraries()

    The factor libraries.

    :returns: ``DataFrame`` with columns name, version, factors (count), description

    **Examples**

    .. lf-examples:: list_factor_libraries

.. py:function:: list_factors(library=None)

    The full names of the factors of ``library``, or of every library.

    :param library: A library name, e.g. ``"system/barra-cne5"``
    :returns: ``list`` of full factor names with their revision (``system/barra-cne5/SIZE@v2.0.0``);
        without ``@revision`` a name reads the current one

    **Examples**

    .. lf-examples:: list_factors
