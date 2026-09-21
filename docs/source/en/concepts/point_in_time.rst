Point-in-time mechanism: as_of
==============================

A backtest needs the securities available at each decision time and the
information then usable. Historical prices combined with today's universe
and revised financials can describe an impossible strategy. Point-in-time
(PIT) queries make the observation time explicit through ``as_of``.

First: exclude future information
---------------------------------

A reporting period is not a publication date. A ``2023q4`` annual report may
be released months later and revised again the following year. Consider this
hypothetical net-profit history, in millions:

.. list-table::
   :header-rows: 1

   * - Period
     - Publication date
     - Net profit
     - Version
   * - 2023q4
     - 2024-04-20
     - 100
     - Original
   * - 2023q4
     - 2025-04-20
     - 80
     - Revision

On 2024-03-31 there is no available report; on 2024-06-30 the usable value is
100; the latest revision is 80. The reporting period stays the same while
the observation time changes. Financial PIT first excludes versions published
after ``as_of``. ``statements="latest"`` selects the latest remaining version;
``statements="all"`` is also bounded by that cutoff.

Next: restore securities that later disappeared
-----------------------------------------------

Starting a historical backtest with today's listed stocks omits later
delistings, mergers and renamed securities, introducing survivorship bias.
It can also include stocks that had not yet listed.

.. list-table::
   :header-rows: 1

   * - Hypothetical security
     - In 2020
     - Today
     - Include in the 2020 universe?
   * - A
     - Listed
     - Delisted
     - Yes
   * - B
     - Listed
     - Listed
     - Yes
   * - C
     - Not yet listed
     - Listed
     - No

Filtering today's B and C cannot recover missing A. PIT must start with the
security directory: reconstruct A and B, then retrieve financials visible at
the same decision time. Codes have validity periods too, so historical
``instruments`` queries need ``as_of`` to resolve renamed or reused codes.

What as_of means in each API
----------------------------

``as_of`` specifies an observation time. The underlying temporal selection
depends on the object being queried:

.. list-table::
   :header-rows: 1
   :widths: 28 38 34

   * - API
     - as_of selects
     - Other time parameters
   * - ``all_instruments`` / ``instruments``
     - Security state and code mappings valid at that business date
     - No separate date argument
   * - ``get_pit_financials_ex`` / ``get_factor``
     - Disclosure versions available by the cutoff
     - start_quarter / end_quarter select reporting periods
   * - ``get_price``
     - No as_of parameter in the current API
     - start_date / end_date select bars; adjust_orig selects an adjustment anchor

Business validity does not establish what the database had ingested on that
date. The upstream instrument model records system knowledge through immutable
dataset versions; reproducibility also requires fixing that version. Index
code mappings support historical dates, but some identity attributes still
come from a current snapshot filtered by lifecycle dates, not full attribute
history.

Omitting ``as_of`` selects current state or the latest version, depending on
the API. Backtests should pass decision times explicitly. Disclosure dates
alone do not establish intraday availability: do not assume that every report
published on a date was available before that day's market open.

Using libfinance
----------------

Reconstruct the universe first, then query financials at the same decision
time. This example prints three securities for readability; a production
universe should not be truncated with ``head(3)``:

.. code-block:: python

   import libfinance as lf

   as_of = "2024-06-28"
   universe = lf.all_instruments(type="CS", market="cn", as_of=as_of)
   print(universe[["order_book_id", "symbol", "listed_date"]].head(3))

   ids = universe["order_book_id"].head(3).tolist()
   for item in lf.instruments(ids, as_of=as_of):
       print(item.order_book_id, item.symbol, item.type)

   if ids:
       financials = lf.get_pit_financials_ex(
           ids, ["net_profit"], "2023q4", "2023q4",
           as_of=as_of, statements="latest",
       )
       print(financials)
       print(lf.get_factor(
           ids, ["net_profit_ttm"], "2024q1", "2024q1", as_of=as_of,
       ))

Inspect identities in the security output and ``info_date`` in financials.
Missing financials may mean no report was available yet; do not backfill with
today's values or assume zero. ``get_factor`` retrieves financial derived
factors, distinct from the exfactor price adjustments in the next chapter.

To compare disclosure versions, hold the security, field and reporting period
fixed and change only the observation time:

.. code-block:: python

   for cutoff in ("2024-03-31", "2024-06-30", None):
       print("as_of =", cutoff)
       print(lf.get_pit_financials_ex(
           "600000.XSHG", ["net_profit"], "2023q4", "2023q4",
           as_of=cutoff, statements="all",
       ))

These calls print actual server results. The earlier values 100 and 80 are
hypothetical, not this security's reported profits.

PIT constrains both who can be selected and what information can be used.
Delisting returns, last trading dates and position handling still require
correct backtest rules. Restoring a historical universe alone does not
eliminate every source of survivorship bias.
