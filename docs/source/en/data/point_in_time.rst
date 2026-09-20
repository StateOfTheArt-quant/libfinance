=====================================
Restatements and ``as_of``
=====================================

Financial data differs from prices in one fundamental way: **prices are final once
set; financial statements get restated.**

A company's 2023 annual report is first published in April 2024, and may later be
rewritten because of audit adjustments, accounting policy changes or
restatements. The database therefore holds **several versions** of the same
quarter.

Which raises a question. When your backtest asks "what was this company's net
profit as of June 2024", do you want

* the version **visible at the time**, in June 2024, or
* the **latest restated** version as of today?

A backtest wants the former. Taking the latter is look-ahead bias — you used
information that did not yet exist.

A real example
==============

Net profit for ``000016.XSHE`` (\*ST Konka A) FY2023 exists here in six versions:

.. code-block:: python

    >>> from libfinance import get_pit_financials_ex
    >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4",
    ...                       statements="all")

.. code-block:: text

      order_book_id quarter  info_date    net_profit  if_adjusted
    0   000016.XSHE  2023q4 2024-04-02 -2.635887e+09            0
    1   000016.XSHE  2023q4 2024-04-29 -2.635887e+09            1
    2   000016.XSHE  2023q4 2024-08-31 -2.635887e+09            1
    3   000016.XSHE  2023q4 2024-10-31 -2.635887e+09            1
    4   000016.XSHE  2023q4 2025-04-15 -2.635887e+09            1
    5   000016.XSHE  2023q4 2026-04-29 -2.730376e+09            1

Look at the last row: in **April 2026**, this 2023 annual report was revised — the
loss grew from 2.636bn to 2.730bn, 3.6% larger.

If you are backtesting 2024 and you used that last number, you used information
that appeared two years later.

``as_of``: the day you are looking back from
============================================

``as_of`` is the parameter that answers this:

.. code-block:: python

    >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4",
    ...                       as_of="2024-06-30")
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000016.XSHE   2023q4  2024-04-29 -2.635887e+09            1

    >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4")
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000016.XSHE   2023q4  2026-04-29 -2.730376e+09            1

Same quarter, same field: seen from June 2024 it is ``-2.636bn``, seen today it is
``-2.730bn``.

.. danger::

    **Omitting ``as_of`` means taking the latest version.** That is right for
    present-day analysis and wrong in a backtest — with nothing to tell you.

    The test is simple: if your code has a "current simulated date", every
    financial query should carry it.

``as_of`` is not ``date``
=========================

These two are easy to conflate:

.. list-table::
    :header-rows: 1
    :widths: 16 40 44

    *   - Parameter
        - Asks about
        - Example
    *   - ``as_of``
        - the **knowledge** cutoff: which day you are looking back from
        - "the version of the annual report published as of 2024-06-30"
    *   - ``date``
        - the **data** date: which day's data you want
        - "index constituents on 2024-06-30"

One is "when did we know it", the other is "when did it happen". Financial data
needs both; prices need only the second.

``info_date`` and ``if_adjusted``
=================================

These two columns tell you which version you are holding:

.. list-table::
    :header-rows: 1
    :widths: 22 78

    *   - Column
        - Meaning
    *   - ``info_date``
        - When this version was published. Always ``<= as_of``
    *   - ``if_adjusted``
        - ``0`` for the originally reported figure, ``1`` for a restated one

Checking ``info_date`` after a query confirms you really got the contemporaneous
version.

``statements``: one version or all of them
==========================================

.. list-table::
    :header-rows: 1
    :widths: 22 78

    *   - Value
        - Returns
    *   - ``"latest"`` (default)
        - One row per quarter — the latest version subject to ``as_of``
    *   - ``"all"``
        - Every revision of that quarter, one row each

Use ``"all"`` when studying restatements themselves (for example, revision
magnitude against subsequent returns). Otherwise the default is what you want.

Quarter format
==============

``start_quarter`` and ``end_quarter`` look like ``2024q1``; case is ignored and
``2024-q1`` is accepted too:

.. code-block:: python

    >>> get_factor("600000.XSHG", ["net_profit_ttm"], "2024q1", "2025q1")
                           net_profit_ttm
    order_book_id quarter
    600000.XSHG   2024q1     1.072960e+11
                  2024q2     1.110050e+11
                  2024q3     1.181000e+11
                  2024q4     1.265060e+11
                  2025q1     1.266220e+11

:func:`~libfinance.get_factor` takes ``as_of`` with identical semantics.

.. tip::

    **Transferable rule**: whenever you receive data that can be restated
    (financials, ratings, index changes, analyst estimates), ask whether it has a
    notion of *version* — and if so, whether the version you are holding is the
    one you could have seen at that point in time.

For the full workflow see :doc:`../howto/pit_backtest`.
