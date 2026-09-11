=======================
calendar
=======================

Main module of the calendar containing:

服务端只出两条原语——全部交易日与它的权威区间；区间切片、前后推、是否交易日都在客户端
本地算（拉一次缓存一天）。所有函数都接受 ``market``，默认 ``"cn"``。

查询落在 release 确认过的区间之外会抛 ``CalendarCoverageError``——没人发布过的日子，
任何答案都是猜的，不会悄悄返回一个变短的结果。


get_all_trading_dates
--------------------------

.. autofunction:: libfinance.api.calendar.get_all_trading_dates


get_calendar_coverage
--------------------------

.. autofunction:: libfinance.api.calendar.get_calendar_coverage


get_trading_dates
--------------------------

.. autofunction:: libfinance.api.calendar.get_trading_dates


get_previous_trading_date
-----------------------------

.. autofunction:: libfinance.api.calendar.get_previous_trading_date



get_next_trading_date
-----------------------

.. autofunction:: libfinance.api.calendar.get_next_trading_date


is_trading_date
-----------------------

.. autofunction:: libfinance.api.calendar.is_trading_date


get_n_trading_dates_until
---------------------------

.. autofunction:: libfinance.api.calendar.get_n_trading_dates_until


count_trading_dates
----------------------------
.. autofunction:: libfinance.api.calendar.count_trading_dates