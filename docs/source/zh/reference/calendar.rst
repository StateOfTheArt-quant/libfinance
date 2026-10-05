交易日历
========================================

.. currentmodule:: libfinance

日历函数默认 ``market="cn"``\ ；美股使用 ``market="us"``\ 。
日期区间包含两端，前后偏移严格排除输入日。详见 :doc:`../data/calendar`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_trading_dates`
      - 查询日期区间内的交易日
    * - :func:`~libfinance.is_trading_date`
      - 判断某一天是否开市
    * - :func:`~libfinance.get_previous_trading_date`
      - 向前偏移 n 个交易日
    * - :func:`~libfinance.get_next_trading_date`
      - 向后偏移 n 个交易日
    * - :func:`~libfinance.get_n_trading_dates_until`
      - 取截至某日的最近 n 个交易日
    * - :func:`~libfinance.count_trading_dates`
      - 统计区间内的交易日数量
    * - :func:`~libfinance.get_all_trading_dates`
      - 取得当前日历包含的全部交易日
    * - :func:`~libfinance.get_calendar_coverage`
      - 确认日历有效区间，避免越界查询

get_trading_dates — 查询日期区间内的交易日
--------------------------------------------------------------

.. autofunction:: get_trading_dates

**示例**

.. lf-examples:: get_trading_dates

结果解读：相同日期区间也可能包含不同交易日：示例突出中美日历在 1 月 15 日的区别。

is_trading_date — 判断某一天是否开市
------------------------------------------------------

.. autofunction:: is_trading_date

**示例**

.. lf-examples:: is_trading_date

结果解读：结果为布尔值，可直接用于条件判断。

get_previous_trading_date — 向前偏移 n 个交易日
------------------------------------------------------------------------------

.. autofunction:: get_previous_trading_date

**示例**

.. lf-examples:: get_previous_trading_date

结果解读：n=1 与 n=3 分别回到上一个和第三个交易日，均不包含输入日。

get_next_trading_date — 向后偏移 n 个交易日
----------------------------------------------------------------------

.. autofunction:: get_next_trading_date

**示例**

.. lf-examples:: get_next_trading_date

结果解读：周五之后的第一个交易日是周一；n=3 是第三个交易日，不是三个自然日。

get_n_trading_dates_until — 取截至某日的最近 n 个交易日
--------------------------------------------------------------------------------------

.. autofunction:: get_n_trading_dates_until

**示例**

.. lf-examples:: get_n_trading_dates_until

结果解读：输入交易日时包含当天；输入周日时窗口截至此前的周五。

count_trading_dates — 统计区间内的交易日数量
------------------------------------------------------------------

.. autofunction:: count_trading_dates

**示例**

.. lf-examples:: count_trading_dates

结果解读：返回整数，不返回日期列表；这里统计的是交易日而非自然日。

get_all_trading_dates — 取得当前日历包含的全部交易日
----------------------------------------------------------------------------

.. autofunction:: get_all_trading_dates

**示例**

.. lf-examples:: get_all_trading_dates

结果解读：示例打印交易日的个数与首尾两天；完整结果是日期索引（\ ``DatetimeIndex``\ ），不是带证券列的 DataFrame。

get_calendar_coverage — 确认日历有效区间，避免越界查询
------------------------------------------------------------------------------

.. autofunction:: get_calendar_coverage

**示例**

.. lf-examples:: get_calendar_coverage

结果解读：边界随数据版本变化；confirmed_through 是日历确认上界，不能当作行情上界。

