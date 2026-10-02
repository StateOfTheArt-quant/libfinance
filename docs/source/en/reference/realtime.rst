=================
Live market data
=================

.. currentmodule:: libfinance

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - Function / class
      - Purpose
    * - :func:`~libfinance.get_last_quotes`
      - Read the latest quote snapshots


Semantics are covered in :doc:`../data/realtime`.

Snapshots
=========

.. py:function:: get_last_quotes(order_book_ids)

    The latest snapshot for each code.

    :param order_book_ids: List of codes
    :returns: ``dict`` keyed by code, with
        :py:class:`~libfinance.subscribe.md_protocol.Quote` values. A value is
        ``None`` when no snapshot is currently available — outside trading hours,
        or on a deployment with no live feed.

Subscriptions
=============

    **Examples**

    Run these blocks in order. Printed results below are **illustrative**, not captured
    from a live service. Values, identifiers and events are not market facts; ellipses
    mark omitted content.

    .. literalinclude:: ../../../../example/python/11_live_quote.py
        :language: python
        :start-after: # [get_last_quotes.1]
        :end-before: # [/get_last_quotes.1]
        :prepend: from libfinance import get_last_quotes

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_last_quotes.1.txt
        :language: text

    .. literalinclude:: ../../../../example/python/11_live_quote.py
        :language: python
        :start-after: # [get_last_quotes.2]
        :end-before: # [/get_last_quotes.2]

    Illustrative printed result:

    .. literalinclude:: ../../../_shared/example_outputs/get_last_quotes.2.txt
        :language: text

    Reading the result: The first block shows the dictionary. The second reads Quote attributes and handles None when no snapshot is available.

    :download:`Download the full example <../../../../example/python/11_live_quote.py>`

.. currentmodule:: libfinance.subscribe.quote_api

.. py:class:: QuoteApi(auto_reconnect=True)

    Client for the market data gateway. No login is needed: it fetches a ticket from
    the libfinance service (a per-IP allowance without login) and renews it before
    it expires. After a disconnect it reconnects, logs in again and re-sends the
    records you missed by sequence number.

    .. py:method:: register_spi(spi)

        Register the callback handler, an instance of :py:class:`~libfinance.subscribe.quote_api.QuoteSpi`.

    .. py:method:: connect(addresses=None, port=None, timeout=3.0)

        Connect to the gateway. Without arguments the address comes from the
        libfinance service together with the ticket; ``"host:port,host:port"`` or
        ``connect(host, port)`` targets specific gateways. Returns ``0`` once
        connected, ``-1`` if not yet (it keeps retrying in the background).

    .. py:method:: login(token=None)

        Optional. Supply your own ticket: a string, or a function returning one
        (called on first login, on every reconnect and before expiry).

    .. py:method:: subscribe(order_book_ids, *, source="")

        Subscribe to securities by order_book_id (``"600519.XSHG"``, one or a list; exchanges may be
        mixed). Every code is checked before anything is sent (``ValueError``). An empty ``source``
        lets the gateway pick and fail over; a named source disables failover. One
        ``on_rsp_subscribe`` per code, carrying its ``order_book_id``.

        Call this inside ``on_rsp_login`` so it is replayed after a reconnect.

    .. py:method:: unsubscribe(order_book_ids, *, source="")

        Cancel a subscription.

    .. py:method:: subscribe_all(market=0, instrument_type=0, data_type=0)

        Subscribe to everything matching market × instrument type × data type.
        ``0`` means unrestricted on that axis. Requires an allowance that
        includes whole-market subscription.

    .. py:method:: unsubscribe_all()

        Cancel every whole-market subscription on this connection. Per-contract
        subscriptions are unaffected.

    .. py:method:: query_sources()

        Query the source directory. The answer arrives via
        ``on_rsp_query_sources``.

    .. py:method:: disconnect()

        Disconnect and stop the background threads.

.. py:class:: QuoteSpi

    Callback base class. Subclass it and override what you need. Callbacks run on
    the background receive thread, so do no slow work inside them.

    Methods: ``on_connected``, ``on_disconnected(reason)``,
    ``on_rsp_login(rsp, request_id)``, ``on_rsp_reauth(rsp)``,
    ``on_session_closed(notice)``, ``on_rsp_subscribe(rsp, request_id)``,
    ``on_rsp_unsubscribe(rsp, request_id)``,
    ``on_rsp_subscribe_all(rsp, request_id)``,
    ``on_rsp_unsubscribe_all(rsp, request_id)``,
    ``on_rsp_query_sources(sources, request_id)``,
    ``on_depth_market_data(quote, envelope)``, ``on_transaction``, ``on_entrust``,
    ``on_tick``, ``on_depth`` (each ``(record, envelope)``), ``on_sequence_gap(gap)``,
    ``on_stream_status(status)``, ``on_heartbeat``.

.. currentmodule:: libfinance.subscribe.md_protocol

.. py:class:: Quote

    One market data snapshot. Fields are listed in :doc:`../data/realtime`.
