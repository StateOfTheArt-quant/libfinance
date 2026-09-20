======================
Connecting to a server
======================

``libfinance`` carries no data of its own — it sends queries to a data service.
So the first thing to do after ``import`` is tell it where that service is.

Connect
=======

Call :func:`~libfinance.init_client` once, **before your first data call**:

.. code-block:: python

    import libfinance

    libfinance.init_client(host="libfinance.tech", port=8080)

.. warning::

    ``init_client`` only takes effect when no connection exists yet. If you have
    already called a data function (which triggers an automatic connection),
    calling ``init_client`` afterwards to switch hosts does **nothing** — and
    reports no error. Put it at the top of your script.

For a self-hosted service, use your own address:

.. code-block:: python

    libfinance.init_client(host="127.0.0.1", port=8080)

How to tell you are connected
=============================

Don't rely on "the next data call didn't fail" — that mixes connection problems
with data problems. Ask directly:

.. code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

Two dates back means: the connection works, the service is answering, and data is
mounted.

When you cannot connect
=======================

For errors like ``Client auto-connect to <host>:<port> failed`` or
``ConnectionError``, work through these in order. Each step has a clear verdict:

.. list-table::
    :header-rows: 1
    :widths: 8 30 62

    *   - Step
        - Check
        - Verdict
    *   - 1
        - Is the port reachable?

          ``telnet <host> 8080``
        - Fails → wrong address, service not running, or a firewall. Stop here;
          the remaining steps don't apply.
    *   - 2
        - Is the service answering?
        - Port opens but calls hang or the connection drops immediately: whatever
          is on that port is **not** this service (for example a load balancer
          with nothing behind it).
    *   - 3
        - Is the request being refused?
        - You get a response but an ``RpcError``: the connection is fine, the
          problem is the request itself. See :doc:`../howto/troubleshooting`.

Query range limits
==================

The server may restrict how far back you can query: the start date is clamped to
roughly the last two years, and anything earlier is silently pulled forward. You
may then get an empty table — and an empty table cannot tell you whether the data
is missing or the range was clamped. The client emits a warning naming the
boundary date when this happens.

Next: :doc:`quickstart`.
