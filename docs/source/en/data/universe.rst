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
        - :func:`~libfinance.get_industry_constituents` / :func:`~libfinance.get_instrument_industry`
        - Full market coverage, several levels and classifications
    *   - Themes
        - :func:`~libfinance.get_theme_constituents`, :func:`~libfinance.get_theme_weights`
        - Theme-driven, numerous, fuzzy boundaries

Index constituents and weights
==============================

.. code-block:: python

    >>> from libfinance import get_index_weights
    >>> w = get_index_weights("000300.XSHG", as_of="2024-02-29")
    >>> w[["order_book_id", "weight", "source", "basis", "date"]].head()
      order_book_id   weight source   basis       date
    0   000001.XSHE  0.00576    CSI  origin 2024-02-29
    1   000002.XSHE  0.00383    CSI  origin 2024-02-29
    2   000063.XSHE  0.00534    CSI  origin 2024-02-29
    3   000069.XSHE  0.00085    CSI  origin 2024-02-29
    4   000100.XSHE  0.00477    CSI  origin 2024-02-29

Weights are normalised:

.. code-block:: python

    >>> w["weight"].sum()
    1.0

.. note::

    **Any trading day works, not just rebalancing dates.**

    Index providers publish weights only on rebalancing dates. Weights for other
    days are derived: take the most recent published snapshot at or before the
    date, re-weight each constituent by its **adjusted** return from that snapshot
    to the target date, then normalise.

    Using adjusted returns is essential — with a bonus issue or split inside the
    window, raw price changes would misread a share-count change as a return.

Omit ``as_of`` for the latest snapshot. The index is named by its ``order_book_id``
(``000300.XSHG``, ``SPX.US``). Each row says where its weight came from: ``basis`` is
``origin`` (published by a data source) or ``reconstructed`` (rebuilt by the index
methodology), ``date`` is the snapshot the weight belongs to (``as_of`` when it was
drifted, with ``DRIFTED`` in ``quality_flags``).

The result carries no index or constituent names — names are security master data;
fetch them with :func:`~libfinance.instruments` if needed.

Industry classification
=======================

An industry is named by an ``order_book_id`` (``<classification code>.<classification>``): Shenwan banks are
``480000.SW``, GICS energy is ``10.GICS``. ``source`` is the classification (``SW``, ``GICS``, ...), ``level`` its depth.

To look up which industries a stock belongs to:

.. code-block:: python

    >>> from libfinance import get_instrument_industry
    >>> get_instrument_industry(["000001.XSHE", "600000.XSHG"], source="SW", level=1, as_of="2024-03-08")
      order_book_id related_order_book_id source market  level
    0   000001.XSHE             480000.SW     SW     CN      1
    1   600000.XSHG             480000.SW     SW     CN      1

Omit ``source`` / ``level`` for every classification and level. ``related_order_book_id`` is the industry code.

To go the other way and list an industry's members, and their weights:

.. code-block:: python

    >>> from libfinance import get_industry_constituents, get_industry_weights
    >>> get_industry_constituents("480000.SW", as_of="2024-03-08")[:6]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE',
     '002839.XSHE', '002936.XSHE']
    >>> get_industry_weights("480000.SW", as_of="2024-03-08")   # each row carries its methodology

.. important::

    Industry membership changes. Historical backtests must pass ``as_of``, or you
    are slicing the past with **today's** classification — another form of
    look-ahead bias.

Themes
======

A theme is one kind of object in the security catalog (``type="theme"``), with codes such as
``300008.THS``; THS is currently the only source. First list the themes from the catalog:

.. code-block:: python

    >>> from libfinance import all_instruments
    >>> all_instruments(type="theme")[["order_book_id", "source", "name"]].head(3)
      order_book_id source   name
    0    300008.THS    THS  新能源汽车
    1    300013.THS    THS    大飞机
    2    300018.THS    THS   参股保险

Then fetch members and weights by theme code:

.. code-block:: python

    >>> from libfinance import get_theme_constituents, get_theme_weights
    >>> members = get_theme_constituents("300008.THS")
    >>> len(members), members[:3]
    (1061, ['000009.XSHE', '000021.XSHE', '000030.XSHE'])
    >>> get_theme_weights("300008.THS")[["order_book_id", "weight", "effective_from"]].head(3)
      order_book_id    weight effective_from
    0   000009.XSHE  0.000943     2026-09-22
    1   000021.XSHE  0.000943     2026-09-22
    2   000030.XSHE  0.000943     2026-09-22

To find the themes a security belongs to, use :func:`~libfinance.get_instrument_themes`.

.. warning::

    **Look theme codes up in the catalog; do not hard-code them.** For a theme that does not
    exist on the day, ``get_theme_constituents`` returns ``None`` without an error:

    .. code-block:: python

        >>> get_theme_constituents("886074.THS") is None
        True

    A mistyped code and "no such theme that day" look the same; check against
    ``all_instruments(type="theme")``.

``as_of`` applies here too: use the membership **known** at that point. Pass it
when building historical universes, for the reasons in :doc:`point_in_time`.
