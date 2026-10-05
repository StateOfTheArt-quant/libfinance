Unified security identifiers <trading_code>.<namespace>
=======================================================

Prices, financials and corporate actions all need an unambiguous query target.
libfinance uses ``<trading_code>.<namespace>``, called ``order_book_id`` in the
API. The trading code is readable; the namespace resolves naming conflicts.
This separates security identity, listing location and market-data coverage.

From conflicting codes to namespaces
------------------------------------

``000001`` alone can mean either the Shanghai Composite Index or Ping An Bank.
The namespace identifies the object; its ``type`` metadata identifies the
kind of object:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - order_book_id
     - Object
     - type
   * - ``000001.XSHG``
     - Shanghai Composite Index
     - ``INDX``: index
   * - ``000001.XSHE``
     - Ping An Bank
     - ``CS``: stock
   * - ``600000.XSHG``
     - Shanghai Pudong Development Bank
     - ``CS``: stock
   * - ``000300.XSHG``
     - CSI 300
     - ``INDX``: index

``XSHG`` does not mean index, and ``XSHE`` does not mean stock. Both namespaces
can contain different instrument types. Price queries use instrument metadata
to distinguish stock data from index data, rather than guessing from digits.

Where XSHG and XSHE come from
-----------------------------

These suffixes come from **ISO 10383**, the Market Identifier Code (MIC)
standard. MICs have four alphanumeric characters. The register assigns
``XSHG`` to the Shanghai Stock Exchange and ``XSHE`` to the Shenzhen Stock
Exchange. These are standard identifiers, not abbreviations invented by
libfinance or indicators of asset type. See the
`ISO MIC register <https://www.iso20022.org/market-identifier-codes>`_.

``US`` comes from the two-letter country codes in
`ISO 3166-1 <https://www.iso.org/iso-3166-country-codes.html>`_.
The namespace is as specific as necessary to resolve naming conflicts.
Shanghai and Shenzhen have overlapping code spaces; US listed equities have
coordinated symbols across listing exchanges. The format and meaning are
consistent, while the namespace granularity follows market structure.

000300: an index is not a stock
-------------------------------

libfinance identifies the CSI 300 as ``000300.XSHG``. The SSE methodology
specifies ``000300`` for Shanghai quotations and ``399300`` for Shenzhen
quotations, with constituents selected from both markets. The ``XSHG`` suffix
therefore means neither a Shanghai stock nor an index limited to Shanghai
constituents. See the
`CSI 300 methodology <https://www.sse.com.cn/market/sseindex/diclosure/c/c_20150911_3984891.shtml>`_.

For an index, the namespace locates an object in a publication or quotation
code system; it does not imply a matching order book. The index, its
constituents and ETFs tracking it are distinct objects with separate codes.
Do not extrapolate from the ``000001`` pair and assume that ``000300.XSHE``
is an existing stock. Consult the security directory for existence and type.

.. code-block:: python

   import libfinance as lf

   for item in lf.instruments([
       "000001.XSHE", "000001.XSHG", "600000.XSHG", "000300.XSHG"
   ]):
       print(item.order_book_id, item.symbol, item.type)

Illustrative output (names follow the server dataset):

.. code-block:: text

   000001.XSHE 平安银行 CS
   000001.XSHG 上证指数 INDX
   600000.XSHG 浦发银行 CS
   000300.XSHG 沪深300 INDX

Inspect all directory entries with trading code ``000300`` instead of
constructing suffixes:

.. code-block:: python

   catalog = lf.all_instruments(market="cn")
   matched = catalog[
       catalog["order_book_id"].str.split(".", regex=False).str[0] == "000300"
   ]
   print(matched[["order_book_id", "symbol", "type"]].to_string(index=False))

Why US equities use US
----------------------

Listing, trading and consolidation answer different questions:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Concept
     - Question
     - Implication
   * - Listing venue
     - Where is the security listed and subject to listing rules?
     - A listing attribute that can change
   * - Trading venue
     - Where was an order executed?
     - One security can trade at several venues
   * - Consolidated tape
     - What do reported trades and quotes across venues show?
     - Data coverage, not another security

**Symbol allocation is coordinated across exchanges.** The NMS plan for
selecting and reserving securities symbols uses ISRA to coordinate symbols
across markets. US listing exchanges do not independently allocate conflicting
root symbols. This supports a national namespace for listed equities, without
claiming that a ticker alone distinguishes every asset class or historical
period. See
`Nasdaq symbol reservations <https://listingcenter.nasdaq.com/SymbolReservationRequest/start/new>`_.

**Listing does not restrict execution to that exchange.** An order in a
Nasdaq-listed stock may reach another exchange, a market maker or an electronic
communications network. One venue's volume cannot be treated as total market
volume. See the
`SEC explanation of market centers <https://www.sec.gov/answers/market.htm>`_.

**Consolidation combines reports.** A Securities Information Processor (SIP)
collects trades and quotes reported by participating markets. The familiar
CTA Tapes A/B and UTP Tape C group securities by listing; they do not contain
only trades executed on the listing exchange. See
`CTA <https://www.ctaplan.com/index>`_ and `UTP <https://www.utpplan.com/>`_.
A consolidated last trade, a venue-specific trade and an official listing
exchange close can also represent different price definitions.

``AAPL.US`` identifies Apple shares in the US code space. Its listing exchange
can be recorded separately as ``XNAS``, while executions may occur at multiple
venues. The suffix does not guarantee that a data feed covers every venue;
coverage belongs in the product specification. If a security transfers its
listing but keeps its ticker, ``.US`` avoids an unnecessary identifier change.

From identifiers to mixed-market queries
----------------------------------------

Complete codes provide the information needed for market routing. Security
queries omit the redundant ``market`` argument. The server can query each
market in a mixed list and combine results, avoiding manual grouping and
conflicting code/market arguments.

.. code-block:: python

   for item in lf.instruments(["000001.XSHE", "AAPL.US"]):
       print(item.order_book_id, item.symbol, item.type)

Calendars and market-wide directories still accept ``market`` to choose a
scope. For example, omitting it from ``all_instruments`` combines the server's
bound markets. Recognizing a namespace does not guarantee that its market or
datasets are available.

Normalization and extensions
----------------------------

The upstream design defines additional mechanisms to keep identifiers
unambiguous:

* Internal punctuation becomes a hyphen: ``BRK.A`` becomes ``BRK-A.US``,
  keeping punctuation inside the ticker separate from the namespace delimiter.
* Instruments needing further disambiguation can use
  ``<trading_code>.<namespace>.<class>``, such as the design example
  ``IBM.US.PR-A``. This optional extension is not a mandatory type suffix
  for existing stocks and indices.
* Source aliases should resolve to a canonical output code. Ambiguous
  resolution should be rejected rather than silently choosing an object.

These are design conventions, not a promise that the client supports every
extended instrument or alias. Use complete ``order_book_id`` values returned
by the directory. Likewise, the upstream design's ``venue`` and ``meta.scope``
examples do not describe parameters or return fields currently offered by
``get_price``.

Readable codes and permanent identity
-------------------------------------

Namespaces resolve conflicts at a point in time. Renaming and historical code
reuse require another layer. The upstream model separates:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Layer
     - Purpose
   * - ``instrument_id``
     - Permanent security identity, preserved across name, code and exchange changes
   * - ``listing_id``
     - A continuous listing relationship at a particular MIC
   * - Code and validity period
     - Which readable code the security used at a given time
   * - External identifier mappings
     - Time-bounded ISIN, FIGI and other mappings connecting data sources

A change from ``FB.US`` to ``META.US`` should preserve the security's permanent
identity. Reassignment of an old ticker to another security must create a
distinct identity rather than splice unrelated price histories together.
The client supports dated instrument information through
``instruments(..., as_of=...)``. Permanent IDs and listing relationships belong
to the underlying model, not separate client query APIs implied by this page.

A company and its securities are also different objects. Ordinary shares,
ADRs and different share classes may be separate securities. Prices belong to
a security; financial statements must be linked to the reporting entity.
Sharing a company does not mean sharing an ``order_book_id``.
