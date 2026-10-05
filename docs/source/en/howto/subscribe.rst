=========================
Receiving live quotes
=========================

**Goal**: connect to the market data gateway, subscribe to a few stocks, and
receive a continuous stream.

Subscriptions are callback-based: you write a handler class and your methods are
invoked as data arrives.

.. note::

    Subscriptions go through the **market data gateway**, which is not the service
    that serves historical data. **You need neither a login nor the gateway
    address**: ``connect()`` fetches a market data ticket from the libfinance
    service, which also tells it where the gateway is; the SDK renews the ticket
    before it expires. Without a login you get a basic allowance per IP; logged-in
    users get their account tier's allowance.

A complete runnable example
===========================

.. code-block:: python

    import signal
    import threading

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

    ORDER_BOOK_IDS = ["600519.XSHG", "000001.XSHE"]   # the codes every libfinance function takes

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())


    class DemoSpi(QuoteSpi):
        def __init__(self, api):
            self.api = api
            self.count = 0

        def on_connected(self):
            print("[client] connected")

        def on_disconnected(self, reason):
            print("[client] disconnected reason=%s, waiting for reconnect…" % reason)

        def on_rsp_login(self, rsp, request_id):
            if rsp.error_id != 0:
                print("[client] login FAIL:", rsp.error_msg)
                stop.set()
                return
            print("[client] login OK")
            # Must be here — reconnects re-fire this, replaying the subscription
            self.api.subscribe(ORDER_BOOK_IDS)

        def on_rsp_subscribe(self, rsp, request_id):
            if rsp.error_id != 0:
                print("[client] subscribe FAIL:", rsp.error_msg)
            else:
                print("[client] subscribed, source=%s" % rsp.source)

        def on_depth_market_data(self, quote, envelope):
            self.count += 1
            print("%s  last=%.2f  volume=%s" % (
                quote.order_book_id, quote.last_price, quote.volume))


    api = QuoteApi()
    api.register_spi(DemoSpi(api))
    api.connect()     # no login needed; api.connect("host:port") targets a specific gateway

    stop.wait()
    api.disconnect()

Three things you must know
==========================

Subscribe inside ``on_rsp_login``
---------------------------------

.. important::

    This is not a style question. After a disconnect the client reconnects and
    logs in again automatically, and a successful login re-fires
    ``on_rsp_login`` — subscriptions placed there are replayed.

    Placed anywhere else, they are lost on reconnect: **the program keeps running,
    the logs look normal, and no quote ever arrives again.** This is the hardest
    kind of failure to notice.

Codes are order_book_ids
------------------------

``subscribe()`` takes the codes every other libfinance function takes, one or a list, exchanges mixed:

.. code-block:: python

    api.subscribe(["600519.XSHG", "000001.XSHE"])
    api.subscribe("600519.XSHG", source="sim")

Quotes, subscription receipts (``rsp.order_book_id``) and gap notices carry the same code. The
gateway serves the A-share and Chinese futures exchanges (XSHG, XSHE, XBSE, CCFX, XSGE, XDCE, XZCE,
XINE); any other suffix raises ``ValueError`` before a request is sent. ``source`` is keyword-only.

Do no heavy work in callbacks
-----------------------------

.. warning::

    Callbacks run on the background receive thread. Writing to a database,
    plotting or running a model inside one blocks the whole quote stream. Push
    into a ``queue.Queue`` and process on another thread.

Source selection
================

.. list-table::
    :header-rows: 1
    :widths: 30 70

    *   - Form
        - Behaviour
    *   - ``api.subscribe(ids)``
        - The gateway picks a source and fails over automatically when it drops
    *   - ``api.subscribe(ids, source="sim")``
        - Only that source, no failover; fails explicitly if it is unavailable

A contract has one route on the gateway, so the two **cannot be mixed**;
conflicting requests fail in ``on_rsp_subscribe`` with ``error_id=5``.

To discover available sources:

.. code-block:: python

    def on_rsp_query_sources(self, sources, request_id):
        for s in sources:
            print(s.source, "healthy" if s.health else "down",
                  "whole market" if s.whole_market else "partial")

    api.query_sources()

Error codes
===========

.. list-table::
    :header-rows: 1
    :widths: 16 84

    *   - ``error_id``
        - Meaning
    *   - 4
        - No usable source
    *   - 5
        - Routing conflict, or the requested source is unavailable
    *   - 6
        - Subscription limit reached (per IP without login, per account tier when logged in)
    *   - 7
        - The market is not covered by your allowance
    *   - 8
        - Whole-market subscription is not allowed
    *   - 9
        - The allowance shrank at ticket renewal and this subscription was withdrawn (arrives in ``on_rsp_unsubscribe``)
    *   - 20 – 24
        - Ticket invalid / expired / unknown key / revoked / too many connections. The SDK fetches a new ticket and retries 21 and 22 once; the others are not retried

Whole-market subscription
=========================

Subscribe to every contract matching "market × instrument type × data type" at
once:

.. code-block:: python

    from libfinance.subscribe.md_protocol import (
        MarketType, SubscribeInstrumentType, SubscribeDataType)

    api.subscribe_all(market=MarketType.SSE,
                      instrument_type=SubscribeInstrumentType.Stock,
                      data_type=SubscribeDataType.Snapshot)

Pass ``All`` on any axis to leave it unrestricted. This requires an allowance that
includes whole-market subscription (the basic allowance without login does not),
otherwise it returns ``error_id=8``.

If you only need the current price
==================================

When you do not need a stream, a snapshot query is simpler:

.. code-block:: python

    >>> from libfinance import get_last_quotes
    >>> get_last_quotes(["600000.XSHG"])
    {'600000.XSHG': None}

A value of ``None`` means no snapshot is available right now (outside trading
hours, or no live feed on this deployment). Check before dereferencing.

Field meanings are in :doc:`../data/realtime`.

C++
===

The C++ client has the same ``QuoteApi`` / ``QuoteSpi`` (``#include <libfinance/libfinance.hpp>``): the same
methods and callbacks, automatic tickets, reconnection and resume, and codes are order_book_ids too.

.. code-block:: cpp

    namespace lf = libfinance;

    struct DemoSpi : lf::QuoteSpi {
      lf::QuoteApi* api = nullptr;
      void on_rsp_login(const lf::LoginRsp& rsp, int) override {
        if (rsp.error_id == 0) api->subscribe({"600519.XSHG", "000001.XSHE"});   // replayed after a reconnect
      }
      void on_depth_market_data(const lf::Quote& q, const lf::RecordEnvelope&) override {
        std::cout << q.order_book_id() << " " << q.last_price << "\n";
      }
    };

    lf::QuoteApi api;
    DemoSpi spi;
    spi.api = &api;
    api.register_spi(&spi);
    api.connect();          // no login needed

Full example: ``example/cpp/12_live_subscription.cpp``.
