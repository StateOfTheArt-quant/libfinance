股本结构
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

所有股本字段单位均为股；总股本、流通 A 股与自由流通股本回答不同的问题。
返回表以 ``(order_book_id, date)`` 为索引。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_shares`
      - 查询总股本、流通股本与自由流通股本的历史变化

get_shares — 查询总股本、流通股本与自由流通股本的历史变化
----------------------------------------------------------------------

.. autofunction:: get_shares

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/4a_shares.py
    :language: python
    :start-after: # [get_shares.1]
    :end-before: # [/get_shares.1]
    :prepend: from libfinance import get_shares

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_shares.1.txt
    :language: text

.. literalinclude:: ../../../../example/4a_shares.py
    :language: python
    :start-after: # [get_shares.2]
    :end-before: # [/get_shares.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_shares.2.txt
    :language: text

.. literalinclude:: ../../../../example/4a_shares.py
    :language: python
    :start-after: # [get_shares.3]
    :end-before: # [/get_shares.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_shares.3.txt
    :language: text

结果解读：所有数值单位均为股。单日查询仍保留证券和日期两层索引；流通 A 股与自由流通股本含义不同。

:download:`下载完整示例 <../../../../example/4a_shares.py>`
