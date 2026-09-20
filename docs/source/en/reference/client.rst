==========================
Connecting and exceptions
==========================

.. currentmodule:: libfinance

Connecting
==========

.. py:function:: init_client(host='libfinance.tech', port=8080)

    Connect to a data service. Call this once, before your first data call.

    :param host: Server hostname
    :param port: Server port
    :returns: ``None``

    Only takes effect when no connection exists yet. If a data call has already
    triggered an automatic connection, calling this again to switch hosts does
    nothing and reports no error.

Exceptions
==========

.. currentmodule:: libfinance.client

.. py:exception:: RpcError

    The server refused the call. ``code`` is the error code, ``message`` the
    reason.

.. currentmodule:: libfinance.api.calendar

.. py:exception:: CalendarCoverageError

    The query falls outside the range the release has confirmed. This is not "that
    day had no trading" — nobody has published that day, so any answer would be a
    guess.

Caching
=======

Reference data (security master, trading calendar, industry classification) is
cached on the client and invalidated when the server's data changes, so repeated
calls are cheap and you do not need your own cache layer.

To force a refetch — normally only when debugging:

.. code-block:: python

    >>> from libfinance.utils.cache import clear_all
    >>> clear_all()

.. currentmodule:: libfinance
