历史行情
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

目前使用 ``frequency="1d"`` 查询日频数据。默认 ``adjust_type="pre"``\ ，
原始成交价格需显式传 ``"none"``\ 。详见 :doc:`../data/price`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_price`
      - 查询日频价格与成交量，选择字段和复权口径
    * - :func:`~libfinance.get_price_coverage`
      - 确认行情更新上界，构造最近交易日窗口

get_price — 查询日频价格与成交量，选择字段和复权口径
----------------------------------------------------------------

.. autofunction:: get_price

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price.1]
    :end-before: # [/get_price.1]
    :prepend: from libfinance import get_price

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price.1.txt
    :language: text

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price.2]
    :end-before: # [/get_price.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price.2.txt
    :language: text

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price.3]
    :end-before: # [/get_price.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price.3.txt
    :language: text

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price.4]
    :end-before: # [/get_price.4]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price.4.txt
    :language: text

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price.5]
    :end-before: # [/get_price.5]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price.5.txt
    :language: text

结果解读：同一证券和日期，改变复权方式会改变价格及成交量；turnover 保持一致。unstack 后每只证券成为一列。

:download:`下载完整示例 <../../../../example/1_get_price.py>`

get_price_coverage — 确认行情更新上界，构造最近交易日窗口
------------------------------------------------------------------------------

.. autofunction:: get_price_coverage

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price_coverage.1]
    :end-before: # [/get_price_coverage.1]
    :prepend: from libfinance import get_price_coverage, get_price, get_n_trading_dates_until

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price_coverage.1.txt
    :language: text

.. literalinclude:: ../../../../example/1_get_price.py
    :language: python
    :start-after: # [get_price_coverage.2]
    :end-before: # [/get_price_coverage.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_price_coverage.2.txt
    :language: text

结果解读：第二段沿用第一段的 coverage；示意中的 end 为 2026-09-18，因此窗口截至该日。实际窗口随版本变化。

:download:`下载完整示例 <../../../../example/1_get_price.py>`
