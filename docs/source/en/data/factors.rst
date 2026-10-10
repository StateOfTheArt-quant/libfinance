============
Factor data
============

Daily factors cover Chinese A-shares and are organized in **libraries**: the Qlib / Alpha158
price-volume factors, the Barra CNE5 style, industry and country factors, and the raw Barra CNE5 and
CNE6 descriptors. factors-daybar computes and publishes them; :func:`~libfinance.get_factor_exposure`
reads them. Each factor's formula and meaning are in :doc:`../reference/factor_dictionary`.

Libraries
=========

.. list-table::
    :header-rows: 1
    :widths: 30 10 60

    *   - Library
        - Factors
        - Contents
    *   - ``system/qlib``
        - 158
        - Qlib Alpha158's daily price-volume factors: candlestick shape, price, rolling statistics
          (5, 10, 20, 30 and 60-session windows). Formulas identical to Qlib's
          (``qlib/contrib/data/loader.py``)
    *   - ``system/alpha158``
        - 158
        - Refers to the same-named ``system/qlib`` factors in Qlib's Alpha158 field order; no new data.
          Reading the whole library gives the columns in the order of Qlib's Alpha158 handler
    *   - ``system/barra-cne5``
        - 42
        - The Barra China equity model CNE5: 10 style factors (SIZE, BETA, MOMENTUM, RESVOL, NLSIZE,
          BTOP, LIQUIDITY, EARNYILD, GROWTH, LEVERAGE), 31 Shenwan 2021 level-1 industry factors and
          the country factor COUNTRY
    *   - ``system/barra-cne5-descriptor``
        - 17
        - CNE5's raw descriptors (LNCAP, BETA, HSIGMA, RSTR, STOM ...), not standardized
    *   - ``system/barra-cne6-descriptor``
        - 36
        - CNE6's raw descriptors: CNE5's plus quality, long-term reversal, seasonality, short-term
          reversal, historical alpha and dividend yield; the 16 defined as in CNE5 are the same data

``system/barra-cne6`` is reserved for CNE6 style factors (not yet available). The current release still
carries the 36 descriptors under that name from before the rename, the same data as
``system/barra-cne6-descriptor``; use the latter and do not rely on the former.

Time-series and cross-sectional factors
=======================================

How a factor is computed decides whether its value depends on what it is compared with:

.. list-table::
    :header-rows: 1
    :widths: 22 38 40

    *   - Kind
        - Includes
        - Behaviour
    *   - Time-series
        - ``system/qlib``, ``system/alpha158``, all descriptors, Barra industry factors
        - Each security uses only its own history; values are computed ahead and stored, independent
          of what else is queried
    *   - Cross-sectional
        - Barra style factors, COUNTRY
        - Values depend on which stocks are in the cross-section and are computed by the server when
          read; ``universe`` sets the cross-section

The default cross-section is **all A-shares that day** (Shanghai, Shenzhen and Beijing exchanges).
With ``universe`` (a list of codes) the whole computation is redone on those stocks; a requested code
outside ``universe`` gets ``NaN`` for cross-sectional factors. For raw values independent of any
cross-section, read the descriptor libraries.

How the Barra CNE5 style factors are computed
---------------------------------------------

1. Each descriptor is winsorized at 3 standard deviations, then standardized: float-cap-weighted mean
   0, equal-weighted standard deviation 1;
2. Descriptors are combined with the weights of the Barra CNE5 handbook; the weights of descriptors
   lacking analyst data (EPFWD, EGRLF, EGRSF) go proportionally to the others in their group;
3. Orthogonalization: RESVOL is the residual of a cross-sectional regression on BETA and SIZE; NLSIZE is
   the residual of SIZE³ on SIZE;
4. Standardized once more.

The result is the standardized exposure, as RQData's ``get_factor_exposure(..., model="v1")``.
Winsorization means the few largest stocks share the same SIZE (they sit on the same bound).

Inputs and conventions
======================

* **Price-volume factors** (Qlib / Alpha158) use **backward-adjusted** daily bars (open, high, low,
  close, volume, VWAP). A suspended day has no bar and gives ``NaN``; windows count sessions, and a
  window not yet full gives ``NaN``.
* **Descriptors** use backward-adjusted bars, the CSI All Share index (000985.XSHG) as the market
  return, daily metrics such as market cap and turnover, and financial statements. Statements are
  point-in-time: session *d* uses only reports announced by *d* (see :doc:`point_in_time`).
* Descriptors that depend only on statements change on announcement days ("step"); every session still
  has a value when read.
* Statements start in 2005; five-year growth descriptors have values from about 2010, and CNE6's
  long-term reversal and seasonality need about five years of history.
* Values are ``float32``. ``NaN`` means the security is in the cross-section that day but the factor
  cannot be computed (suspended, newly listed, missing statements).

Names and versions
==================

Factor names are written in full; there are no short names:

* a library: ``owner/library``, e.g. ``system/barra-cne5``, expands to all its factors, in the
  library's order;
* a factor: ``owner/library/factor``, e.g. ``system/barra-cne5/SIZE``;
* a version: append ``@revision``, e.g. ``system/barra-cne5/SIZE@v2.0.0``; without it the current
  version is read.

:func:`~libfinance.list_factors` returns full names with their versions. Library versions follow
semantic versioning: adding factors is a minor bump, removing or changing them a major one. Pin the
version in code when results must be reproducible.

Coverage
========

The factor data has a cutoff per market (``markets.CN.cutoff``), which may be earlier than the price
data's. A range beyond the coverage is refused rather than answered with a shorter table:

.. code-block:: python

    >>> get_factor_exposure("600000.XSHG", "system/alpha158/KMID", "2026-09-16", "2026-09-23")
    RpcError(code=2001): system/alpha158/KMID covers 2000-01-04 to 2026-09-10 in the CN store,
    not 2026-09-16 to 2026-09-23

The range in the message is that factor's current coverage.

Free tier
=========

Without login, ``start_date`` is clamped to one year before today and a call takes at most 300 codes;
the client warns when a request is clamped.
