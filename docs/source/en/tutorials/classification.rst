Indices, industries and themes: three ways to group stocks
============================================================

Research keeps asking "which stocks belong with this one". Indices, industries and themes (the
"concepts" of the A-share market) all answer it, but they are drawn by different people, by different
rules, for different purposes. Mixing them up gives conclusions that sound right and do not hold:
backtesting three years ago on today's theme lists, using index membership as an industry, or putting
one stock into two "mutually exclusive" industries.

How they differ:

.. list-table::
    :header-rows: 1
    :widths: 16 28 28 28

    *   -
        - Index
        - Industry
        - Theme (concept)
    *   - Drawn by
        - Index companies: CSI, CNI, S&P Dow Jones, ...
        - Classification systems: Shenwan, GICS, ...
        - Data vendors or market narrative: Tonghuashun, ...
    *   - By what rule
        - A published selection rule: size, liquidity, financials
        - Main business, usually by revenue mix
        - Business links, policy, technology or events
    *   - A stock belongs to
        - Any number of indices, or none
        - **Exactly one** node per level of one system
        - Any number of themes
    *   - Weights
        - Yes, by the index methodology
        - No, member lists only
        - No, member lists only
    *   - Changes
        - Scheduled reviews, e.g. twice a year for the CSI 300
        - Rarely; occasional system revisions, reclassification when a firm changes business
        - Created and reshuffled at any time
    *   - Typical use
        - Benchmarks, universes, hedging
        - Industry neutrality, rotation, risk models
        - Hot topics and event studies
    *   - libfinance code
        - ``000300.XSHG``, ``SPX.US``
        - ``480000.SW``, ``45.GICS``
        - ``300008.THS``

In libfinance the three are queried with the same shape of function (what a security belongs to, what an
object contains, the constituent weights), all answering with the facts of ``as_of``; see
:doc:`../reference/classification`.

Indices: a basket plus a set of rules
------------------------------------------------

An index is more than a member list. It has three parts:

- **A selection rule**: which stocks get in. The CSI 300 takes 300 large, liquid stocks from Shanghai and
  Shenzhen; the CSI 500 takes the next 500; the S&P 500 is picked by a committee on size, liquidity and
  earnings.
- **A weighting scheme**: how much each counts. Most common is free-float market-cap weighting; the Dow Jones
  Industrial Average is price weighted; there are also equal weights, dividend weights, and modified cap
  weights that cap single constituents.
- **A base date and value**: when and from what level it starts. Levels are comparable only within one
  index: CSI 300 at 4,000 is not "higher" than the SSE Composite at 3,000.

By selection rule, indices are roughly **broad market** (CSI 300, CSI 1000, S&P 500: one market or size
segment), **sector** (CSI Banks), **style and strategy** (dividend, value, low volatility) and **thematic**
(CSI New Energy). Two more things to know:

- **Price index versus total return index.** The level you usually see is a price index: dividends paid by
  constituents are not added back, so over long periods it understates the real return. A price index as a
  benchmark leaves the dividends out of the benchmark.
- **Levels before launch are back-calculated.** For an index launched in 2014 with a 2004 base date, the
  2004–2014 levels were computed afterwards by applying the rules; nobody could invest in it at the time.

**Typical uses**: a benchmark ("beat the CSI 300"); a universe ("pick stocks within the CSI 800"); hedging
(index futures against a portfolio's market exposure).

**The trap**: membership changes. Backtesting 2018 on today's CSI 300 picks only "companies that later grew
large", which is textbook survivorship bias. Build historical universes with
``get_index_constituents(..., as_of=...)``.

Industries: a mutually exclusive, exhaustive tree
-------------------------------------------------

An industry classification sorts stocks into a tree by main business (usually by revenue mix). Two
properties set it apart from indices and themes:

- **Mutually exclusive**: at one level of one system, a stock belongs to one industry.
- **Exhaustive**: every stock has an industry.

So the industries at one level cut the whole market into non-overlapping pieces, which is what "industry
neutral" relies on: you can treat each industry separately without counting anything twice.

.. list-table::
    :header-rows: 1
    :widths: 12 14 74

    *   - System
        - Market
        - Notes
    *   - Shenwan SW
        - A-shares
        - By Shenwan Hongyuan Research, the standard for A-share research. Three levels; revised in 2021,
          when level 1 went from 28 to 31 industries
    *   - GICS
        - Global
        - By MSCI and S&P Dow Jones Indices; four levels with 11 sectors; the institutional standard
    *   - ICB
        - Global
        - FTSE Russell's Industry Classification Benchmark; four levels
    *   - NAICS
        - North America
        - North American Industry Classification System, a statistical classification by production
          activity, 2- to 6-digit codes
    *   - SIC
        - US
        - Standard Industrial Classification; older, still used in SEC filings

**Typical uses**:

- **Industry neutralization.** If a stock-selection factor favours banks, much of its return may be the bank
  sector moving, not selection skill. Regressing on industry dummies and keeping the residual, or ranking
  within each industry, removes that part.
- **Risk models.** Barra CNE5's 31 industry factors are dummies of the Shenwan level-1 industries; see
  :doc:`factors`.
- **Rotation and comparison.** Valuations compare meaningfully only within an industry: a bank's P/E and a
  software company's P/E are different things.

**The trap**: classifications change. Firms that change business get reclassified, and the systems
themselves get revised: Shenwan had 400 nodes before its 2021 revision and 608 after, and the former
"Mining" was split into "Coal" and "Petroleum & Petrochemicals". Backtesting the past with today's
industries classifies the companies of the time by a business mix known only later. Use
``get_instrument_industry(..., as_of=...)`` for the industry at the time; for long studies spanning a
revision, decide first which edition to use and how to map between them.

Themes (concepts): stocks gathered around a story
-------------------------------------------------

A theme gathers the stocks related to one story: new-energy vehicles, large aircraft, Beijing–Tianjin–Hebei
integration, computing power, ... It aims to be neither exclusive nor exhaustive:

- **Many-to-many**: one stock can belong to dozens of themes; a large theme can have over a thousand
  members (new-energy vehicles has about 1,000).
- **Driven by narrative**: when a policy lands, a technology breaks through or an event happens, vendors
  create themes and move members in and out, with a lot of judgement involved.
- **No weights**: member lists only. libfinance gives equal weights derived from the list
  (``derived_equal_weight``), not vendor weights.

**Typical uses**: tracking hot topics and money rotation; event studies (how related stocks react to a
policy); explaining short-term co-movement, such as why several seemingly unrelated stocks hit the limit
up on the same day.

**The trap**: of the three, themes carry **the most future information**. Many themes are created after the
rally they describe, and members are often added after the fact; backtesting the past with today's theme
lists means knowing in advance which stocks the market would later lump together. Theme data in
libfinance starts only recently (an earlier ``as_of`` raises ``CoverageError``); it suits research on the
present, not long backtests.

Which to use
------------------------------------------------

.. list-table::
    :header-rows: 1
    :widths: 40 20 40

    *   - What you are doing
        - Use
        - Watch out for
    *   - Measuring a strategy, choosing a benchmark
        - Index
        - Price indices leave out dividends
    *   - Fixing a historical universe
        - Index constituents
        - Pass ``as_of``, or suffer survivorship bias
    *   - Removing industry exposure, controlling portfolio risk
        - Industry
        - One system, one level; pass ``as_of``
    *   - Studying hot topics, events, short-term co-movement
        - Theme
        - Short history; not for long backtests

Code tables
------------------------------------------------

- :doc:`../reference/index_meta`: every index, and which have constituent data
- :doc:`../reference/industry_meta`: every node of Shenwan, GICS, ICB, NAICS and SIC
- :doc:`../reference/theme_meta`: every Tonghuashun theme
- What the returned columns mean: the "Indices, industries and themes" section of :doc:`../reference/fields`
