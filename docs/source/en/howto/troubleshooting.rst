===============
Troubleshooting
===============

Organised by **symptom**: find what you are seeing and start there.

I get an empty table
====================

Empty tables are the worst case because they carry no explanation. Work down in
order of likelihood:

.. list-table::
    :header-rows: 1
    :widths: 30 34 36

    *   - Possible cause
        - How to confirm
        - Fix
    *   - You passed an **index** code
        - Is ``instruments(code).type`` equal to ``INDX``?
        - :func:`~libfinance.get_price` serves stocks only. For index membership
          use :func:`~libfinance.get_index_weights`
    *   - The concept id does not exist
        - Look for an "unknown concept_id" warning
        - Take ids from :func:`~libfinance.get_concept_meta`; don't hard-code them
    *   - The stock did not trade in that range
        - Check ``listed_date`` / ``de_listed_date`` via
          :func:`~libfinance.instruments`
        - Use a different range
    *   - The range was clamped by a server-side limit
        - Look for a warning naming the earliest queryable date
        - Move ``start_date`` inside that boundary, see
          :doc:`../getting_started/connect`
    *   - That market has no such data
        - Try once with a market known to be supported
        - See the availability table in :doc:`us_market`

.. tip::

    **Empty table vs error**: these APIs aim to make "the data is not available"
    an error and "there genuinely were no events" an empty table. So when you get
    an empty table, first assume the query succeeded and the range really is
    empty.

The numbers don't match what I expected
=======================================

.. list-table::
    :header-rows: 1
    :widths: 32 68

    *   - Symptom
        - Cause
    *   - Close is noticeably below my charting software
        - The default is **forward-adjusted**. For traded prices pass
          ``adjust_type="none"`` — see :doc:`../data/price`
    *   - Volume doesn't match my charting software
        - Volume is adjusted too. Compare with ``adjust_type="none"``
    *   - ``close * volume`` isn't the turnover
        - Use the ``turnover`` column
    *   - A big "crash" one day with no news
        - Check whether it was an ex-date:
          :func:`~libfinance.get_dividends`, see :doc:`../data/corporate_actions`
    *   - Backtest returns look implausibly good
        - Suspect look-ahead bias: did financial queries carry ``as_of``, did the
          universe carry ``date``? See :doc:`pit_backtest`
    *   - Financials differ from the published annual report
        - You may have a restated version. Check ``info_date`` and ``if_adjusted``

Reading common errors
=====================

.. list-table::
    :header-rows: 1
    :widths: 42 58

    *   - Error
        - Meaning and fix
    *   - ``Client auto-connect to ... failed``
        - Not connected yet. Call :func:`~libfinance.init_client` **before** your
          first query — see :doc:`../getting_started/connect`
    *   - ``... is outside coverage ...; a date this release does not reach is
          not a date with no trading``
        - ``end_date`` exceeds price coverage. Ask
          :func:`~libfinance.get_price_coverage` for the bound, see
          :doc:`../data/freshness`
    *   - ``CalendarCoverageError: ... 超出 release 确认范围``
        - You asked about a date the calendar has not confirmed. Check
          :func:`~libfinance.get_calendar_coverage`
    *   - ``order_book_ids: at least one valid instrument expected``
        - None of the codes resolved. Look above for "invalid order_book_id"
          warnings — usually a spelling or suffix problem
    *   - ``frequency='5d' 不支持；上游目前只有日频 artifact``
        - Daily bars only. Use ``frequency="1d"``
    *   - ``has N corporate action(s) with no factor in this release``
        - Back-adjustment spans an unpriceable historical event. The message names
          a safe start date; re-query from there
    *   - ``命名空间 'xxx' 没有 market='us' 的 provider``
        - That function has no data for this market, see :doc:`us_market`
    *   - ``AmbiguousMarketError: ... 绑定了多个市场``
        - Pass ``market=`` explicitly
    *   - ``RpcError(code=1201)`` / ``(code=1202)``
        - The server refused this call's permissions; contact the service administrator
    *   - ``Array type doesn't match type of values set``
        - A server-side error, most often from calling a financial function for an
          unsupported market

I got ``None`` back
===================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    *   - Situation
        - Cause
    *   - ``instruments("600000")`` returns ``None``
        - The code has no suffix. Use ``"600000.XSHG"``
    *   - ``instruments(delisted_code)`` returns ``None``
        - Not present in today's universe. Pass ``date=`` to resolve historically,
          see :doc:`../data/instruments`
    *   - ``get_last_quotes`` values are ``None``
        - No snapshot available right now (outside trading hours, or no live feed)

No quotes arriving on a subscription
====================================

.. list-table::
    :header-rows: 1
    :widths: 36 64

    *   - Check
        - Note
    *   - Is the subscribe call inside ``on_rsp_login``?
        - Anywhere else and it is lost after a reconnect, **with no error at all**
    *   - ``error_id`` in ``on_rsp_subscribe``
        - 4 no source, 5 routing conflict, 6 quota exceeded
    *   - Did you include a suffix on the code?
        - ``subscribe()`` wants the bare code, with the exchange passed separately
    *   - Anything blocking in the callback?
        - Callbacks run on the receive thread; slow work stalls the stream

See :doc:`subscribe`.

Still stuck
===========

Include this with your report — it is far more useful than "I can't get data":

.. code-block:: python

    import libfinance
    from libfinance import get_calendar_coverage, get_price_coverage

    print("version:", libfinance.__version__)
    print("calendar coverage:", get_calendar_coverage())
    print("price coverage:", get_price_coverage())
    # plus your full call and the full error, warnings included
