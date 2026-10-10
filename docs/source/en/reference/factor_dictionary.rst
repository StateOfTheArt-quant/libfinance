=================
Factor dictionary
=================

Each factor's group, formula, meaning, lookback (sessions) and storage. The tables are generated from
the factor registry, with the meanings in Chinese. Conventions and computation: :doc:`../data/factors`.

Read a factor by its full name, ``system/<library>/<factor>``, e.g. ``system/qlib/KMID`` or
``system/barra-cne5/SIZE``. Storage: **dense** is one value per session; **step** is stored only when it
changes (statements, industry changes) and still has a value on every session when read;
**runtime** is cross-sectional, computed when read over ``universe`` and not stored.

Qlib and Alpha158
=================

The 158 price-volume factors of ``system/qlib``. ``system/alpha158`` refers to them in Qlib's Alpha158
field order, with the same names and data (``system/alpha158/KMID`` is ``system/qlib/KMID``). Formulas
use Qlib expressions: ``$close`` and the like are backward-adjusted prices, ``Ref($close, 5)`` is the
value 5 sessions earlier, ``Mean``, ``Std``, ``Corr`` and the like are rolling statistics.

.. include:: ../../../_shared/tables/factors/qlib.en.rst

Barra CNE5
==========

``system/barra-cne5``: style factors are standardized exposures (float-cap-weighted mean 0,
equal-weighted standard deviation 1); industry factors are Shenwan 2021 level-1 dummies; COUNTRY is 1
for every stock in the cross-section.

.. include:: ../../../_shared/tables/factors/barra-cne5.en.rst

Barra CNE5 descriptors
======================

``system/barra-cne5-descriptor``: raw values without cross-sectional processing. "Group" is the style
factor a descriptor belongs to. Notation: *r* is the daily return of the backward-adjusted close,
*r_m* that of the CSI All Share index, ewm an exponentially weighted window (weight
0.5^(days ago / half-life), truncated).

.. include:: ../../../_shared/tables/factors/barra-cne5-descriptor.en.rst

Barra CNE6 descriptors
======================

``system/barra-cne6-descriptor``: same notation. Descriptors defined as in CNE5 are the same data.

.. include:: ../../../_shared/tables/factors/barra-cne6-descriptor.en.rst
