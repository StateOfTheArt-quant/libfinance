交易日历
========================================

.. currentmodule:: libfinance

日历函数默认 ``market="cn"``；美股使用 ``market="us"``。
日期区间包含两端，前后偏移严格排除输入日。详见 :doc:`../data/calendar`。

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

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_trading_dates.1]
    :end-before: # [/get_trading_dates.1]
    :prepend: from libfinance import get_trading_dates

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_trading_dates.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_trading_dates.2]
    :end-before: # [/get_trading_dates.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_trading_dates.2.txt
    :language: text

结果解读：相同日期区间也可能包含不同交易日：示例突出中美日历在 1 月 15 日的区别。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

is_trading_date — 判断某一天是否开市
------------------------------------------------------

.. autofunction:: is_trading_date

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [is_trading_date.1]
    :end-before: # [/is_trading_date.1]
    :prepend: from libfinance import is_trading_date

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/is_trading_date.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [is_trading_date.2]
    :end-before: # [/is_trading_date.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/is_trading_date.2.txt
    :language: text

结果解读：结果为布尔值，可直接用于条件判断。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

get_previous_trading_date — 向前偏移 n 个交易日
------------------------------------------------------------------------------

.. autofunction:: get_previous_trading_date

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_previous_trading_date.1]
    :end-before: # [/get_previous_trading_date.1]
    :prepend: from libfinance import get_previous_trading_date

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_previous_trading_date.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_previous_trading_date.2]
    :end-before: # [/get_previous_trading_date.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_previous_trading_date.2.txt
    :language: text

结果解读：n=1 与 n=3 分别回到上一个和第三个交易日，均不包含输入日。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

get_next_trading_date — 向后偏移 n 个交易日
----------------------------------------------------------------------

.. autofunction:: get_next_trading_date

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_next_trading_date.1]
    :end-before: # [/get_next_trading_date.1]
    :prepend: from libfinance import get_next_trading_date

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_next_trading_date.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_next_trading_date.2]
    :end-before: # [/get_next_trading_date.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_next_trading_date.2.txt
    :language: text

结果解读：周五之后的第一个交易日是周一；n=3 是第三个交易日，不是三个自然日。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

get_n_trading_dates_until — 取截至某日的最近 n 个交易日
--------------------------------------------------------------------------------------

.. autofunction:: get_n_trading_dates_until

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_n_trading_dates_until.1]
    :end-before: # [/get_n_trading_dates_until.1]
    :prepend: from libfinance import get_n_trading_dates_until

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_n_trading_dates_until.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_n_trading_dates_until.2]
    :end-before: # [/get_n_trading_dates_until.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_n_trading_dates_until.2.txt
    :language: text

结果解读：输入交易日时包含当天；输入周日时窗口截至此前的周五。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

count_trading_dates — 统计区间内的交易日数量
------------------------------------------------------------------

.. autofunction:: count_trading_dates

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [count_trading_dates.1]
    :end-before: # [/count_trading_dates.1]
    :prepend: from libfinance import count_trading_dates

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/count_trading_dates.1.txt
    :language: text

结果解读：返回整数，不返回日期列表；这里统计的是交易日而非自然日。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

get_all_trading_dates — 取得当前日历包含的全部交易日
----------------------------------------------------------------------------

.. autofunction:: get_all_trading_dates

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_all_trading_dates.1]
    :end-before: # [/get_all_trading_dates.1]
    :prepend: from libfinance import get_all_trading_dates

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_all_trading_dates.1.txt
    :language: text

结果解读：结果是日期索引，不是带证券列的 DataFrame；省略号代表中间日期。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`

get_calendar_coverage — 确认日历有效区间，避免越界查询
------------------------------------------------------------------------------

.. autofunction:: get_calendar_coverage

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_calendar_coverage.1]
    :end-before: # [/get_calendar_coverage.1]
    :prepend: from libfinance import get_calendar_coverage

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_calendar_coverage.1.txt
    :language: text

.. literalinclude:: ../../../../example/0b_trading_calendar.py
    :language: python
    :start-after: # [get_calendar_coverage.2]
    :end-before: # [/get_calendar_coverage.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_calendar_coverage.2.txt
    :language: text

结果解读：边界随数据版本变化；confirmed_through 是日历确认上界，不能当作行情上界。

:download:`下载完整示例 <../../../../example/0b_trading_calendar.py>`
