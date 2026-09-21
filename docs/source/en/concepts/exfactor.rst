High-quality adjustment factors: exfactor
=========================================

A price move from 10 to 9 need not mean a 10% shareholder loss. A dividend of
1 per share transfers value into a cash entitlement. A 10-for-10 bonus issue
doubles the share count and halves the theoretical per-share price.
Unadjusted price ratios can mistake these mechanical changes for losses.

Adjustment factors translate prices to a common basis while retaining market
moves. This chapter uses independently constructed teaching data to explain
events, factors and price changes in sequence. These are not
historical prices of a real security and can be reproduced without a server.

A cash dividend followed by bonus shares
----------------------------------------

Assume no taxes or fees, no additional market move on the two ex-dates, and
separate dates for the dividend and bonus issue:

.. list-table::
   :header-rows: 1

   * - Time
     - Event
     - Unadjusted price
   * - D0, D1
     - Before events
     - 10
   * - D2
     - First event: cash dividend of 1 per share
     - 10 − 1 = 9
   * - D3
     - Market gain of 10%
     - 9 × 1.1 = 9.9
   * - D4
     - Second event: 10 bonus shares for every 10 held
     - 9.9 / 2 = 4.95
   * - D5
     - Market gain of 10%
     - 4.95 × 1.1 = 5.445

For 100 shares, D1 equity value is 1,000. D2 has 900 in shares plus a cash
entitlement of 100. D3 equity value is 990; D4 has 200 shares worth 4.95 each,
also 990. The apparent 10% and 50% losses are mechanical. Actual cash receipt
depends on the payment date, which differs from the ex-date.

From event factors to cumulative factors
----------------------------------------

libfinance exfactor uses the ``PRIOR_CLOSE`` convention: an event factor is
the prior close divided by the theoretical ex-price. It is the reciprocal
of a backward-adjustment multiplier applied to earlier prices. Check factor
direction before comparing vendors.

.. math::

   f_{event} = \frac{P_{prev}}{P_{ex,theoretical}},
   \qquad F(t) = \prod_{ex\_date \le t} f_{event}

The dividend factor is ``10 / 9`` and the bonus factor is ``2``. The cumulative
factor is 1 before D2, ``10 / 9`` at D2 and D3, and ``20 / 9`` from D4 onward.
Events take effect on the ex-date, not the announcement or record date.

Actual ex-date prices can still move with the market. The theoretical price
removes the corporate-action component; it does not force daily returns to
zero.

.. note::

   **Complex corporate actions require more than multiplying ratios.** Rights
   issues need subscription-price, effective-allotment and share-count checks.
   Spinoffs require valuing the distributed security per original share, with
   observable prices distinguished from estimates carrying a valuation basis
   and source. Same-day cash, bonus and rights events must share a consistent
   per-share basis and effective date to avoid ordering errors or double adjustments.

   The factor pipeline aligns security identities, event terms and reference
   prices, handles revisions, cancellations and duplicates, and cross-checks
   available exchange reference information. Pending, incomplete and unpriceable
   events are distinguished from no action. Adjustment queries spanning
   unpriceable events are blocked instead of filled with plausible defaults.
   Event-family coverage remains specific to each dataset.

   Use :func:`~libfinance.get_ex_factor` to inspect event factors, cumulative factors and
   ex-dates. Unpriced events in the cumulative history raise an error; use
   corporate-action APIs to examine the corresponding events.


Three prices, two anchors
-------------------------

For raw price ``P(t)`` and anchor date ``b``:

.. math::

   P_{adjusted}(t;b) = P(t)\frac{F(t)}{F(b)}

.. list-table::
   :header-rows: 1

   * - Mode
     - Calculation in this example
     - Preserves
   * - Unadjusted: ``none``
     - P(t)
     - Historical traded price scale, including ex-date gaps
   * - Latest-anchor adjustment: ``pre``
     - P(t) × F(t) / F(D5)
     - D5 price; earlier prices are rescaled
   * - Initial-anchor adjustment: ``post``
     - P(t) × F(t)
     - Price before the first event; later prices are rescaled

The initial cumulative factor is 1 here. On the server, the ``post`` anchor
is before the release's first event, not the first day of each query window.

.. literalinclude:: ../../../_shared/figures/exfactor-example.txt
   :language: text

At D2 the prices are 9, 4.5 and 10; at D4 they are 4.95, 4.95 and 11.
The two adjusted series differ by a constant multiplier over a fixed dataset,
so their adjacent returns agree while their price levels differ. New events
can change the default latest anchor and therefore historical ``pre`` prices.

.. figure:: ../../../_shared/figures/exfactor-example.svg
   :alt: Raw, latest-anchor and initial-anchor price series, with mechanical dividend and bonus gaps removed from adjusted returns.
   :width: 100%

   Gray: raw prices. Green: pre. Orange: post. Mechanical gaps at D2 and D4
   disappear; the two genuine 10% market gains remain.

Download the :download:`CSV <../../../_shared/figures/exfactor-example.csv>`,
:download:`PNG <../../../_shared/figures/exfactor-example.png>` and
:download:`reproduction script <../../../_shared/generate_exfactor_example.py>`.
The script generates both table and chart and checks event continuity,
anchor prices and the constant ratio between adjusted series.

Adjusted prices are not a cash ledger. If the 100 dividend remains in cash,
D5 wealth is ``200 × 5.445 + 100 = 1,189``, a gain of 18.9%, whereas adjusted
prices rise 21%. Payment timing, taxes, reinvestment and share counts require
separate portfolio accounting; adjusted returns do not automatically equal
realized account returns.

Requesting all three series in libfinance
-----------------------------------------

``get_price`` combines raw bars and exfactor. This real-security example
prints server results, not the synthetic numbers above:

.. code-block:: python

   import pandas as pd
   import libfinance as lf

   prices = {}
   for mode in ("none", "pre", "post"):
       prices[mode] = lf.get_price(
           "600000.XSHG", "2023-07-17", "2023-07-25",
           fields=["close"], adjust_type=mode,
           adjust_orig="2023-07-25" if mode == "pre" else None,
       )["close"]
   print(pd.concat(prices, axis=1).round(4))
   print(lf.get_ex_factor("600000.XSHG", "2023-07-17", "2023-07-25"))
   print(lf.get_dividends(
       "600000.XSHG", start_date="2023-07-17", end_date="2023-07-25",
   ))

``get_ex_factor`` returns an ``ex_date`` index and the columns ``order_book_id``,
``ex_factor`` and ``ex_cum_factor``. The factor columns correspond to ``f_event``
and ``F(t)``. Cumulative values start at 1 before the first event in the dataset
release, not at the query start. Unpriced history also blocks cumulative values
when it predates the query window.
Both CN and US provide event and cumulative factors. See
:doc:`../reference/corporate_actions` for fields and examples with printed output.

``adjust_orig`` selects a ``pre`` anchor. Its default is the factor release's
cutoff, not automatically ``end_date``. An explicit anchor helps comparison
but is not a knowledge cutoff or an equivalent to ``as_of``. Reproducibility
also requires fixed dataset versions.

The current client inversely scales volume with the price factor and leaves
``turnover`` unchanged. Cash dividends do not actually increase shares traded;
use ``adjust_type="none"`` when studying actual traded volume.

Quality requires traceability and validation
--------------------------------------------

A smooth curve alone is insufficient. The factor pipeline must establish:

* **Identity continuity:** connect factors to permanent security identities
  and resolve codes at the query date, avoiding renaming and code-reuse errors.
* **Correct events:** validate ex-dates, cash amounts, share ratios and event
  status; combine same-day actions and avoid duplicate multiplication.
* **Explainable calculations:** preserve pricing inputs, event terms,
  source and status, and cross-check available exchange reference information.
* **Explicit gaps:** reject uncovered periods and unpriceable events rather
  than treating them as no action. A factor of 1 needs evidence of no action.

Revisions and cancellations require recomputing the cumulative factors from
the selected version, not appending another event. Raw prices, event records,
anchor and dataset version together determine the result.
