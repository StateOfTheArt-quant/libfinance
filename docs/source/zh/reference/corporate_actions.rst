5 公司行动信息
========================================

.. currentmodule:: libfinance

四个函数使用同一组参数：证券、事件日期区间、字段与知识截止日。
市场由代码自动推断；混合市场列表按市场查询后合并。不支持的市场会明确报错。
``start_date/end_date`` 限制事件窗口，``as_of`` 限制当时已知的信息。
分拆仅适用于美股。返回事件表，具体字段见 :doc:`fields`。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_dividends`
      - 查询现金分红及送转分配事件
    * - :func:`~libfinance.get_splits`
      - 查询拆股与送转比例
    * - :func:`~libfinance.get_allotments`
      - 查询配股事件
    * - :func:`~libfinance.get_spinoffs`
      - 查询美股分拆事件及其估值依据

get_dividends — 查询现金分红及送转分配事件
----------------------------------------------------------

.. autofunction:: get_dividends

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_dividends.1]
    :end-before: # [/get_dividends.1]
    :prepend: from libfinance import get_dividends

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_dividends.1.txt
    :language: text

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_dividends.2]
    :end-before: # [/get_dividends.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_dividends.2.txt
    :language: text

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_dividends.3]
    :end-before: # [/get_dividends.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_dividends.3.txt
    :language: text

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_dividends.4]
    :end-before: # [/get_dividends.4]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_dividends.4.txt
    :language: text


结果解读：前几段展示全历史、字段筛选、知识截止；最后一段展示中美市场合并，order_book_id 区分证券。示意数值不代表证券的真实分红。

:download:`下载完整示例 <../../../../example/corporate_actions.py>`

get_splits — 查询拆股与送转比例
--------------------------------------------

.. autofunction:: get_splits

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_splits.1]
    :end-before: # [/get_splits.1]
    :prepend: from libfinance import get_splits

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_splits.1.txt
    :language: text

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_splits.2]
    :end-before: # [/get_splits.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_splits.2.txt
    :language: text

结果解读：ratio_from 与 ratio_to 表示变动前后的股数比例；表中的事件仅用于说明结构。

:download:`下载完整示例 <../../../../example/corporate_actions.py>`

get_allotments — 查询配股事件
----------------------------------------------

.. autofunction:: get_allotments

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_allotments.1]
    :end-before: # [/get_allotments.1]
    :prepend: from libfinance import get_allotments

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_allotments.1.txt
    :language: text

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_allotments.2]
    :end-before: # [/get_allotments.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_allotments.2.txt
    :language: text

结果解读：缩小窗口后可能没有事件。空 DataFrame 与查询失败是不同情况。

:download:`下载完整示例 <../../../../example/corporate_actions.py>`

get_spinoffs — 查询美股分拆事件及其估值依据
----------------------------------------------------------

.. autofunction:: get_spinoffs

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/corporate_actions.py
    :language: python
    :start-after: # [get_spinoffs.1]
    :end-before: # [/get_spinoffs.1]
    :prepend: from libfinance import get_spinoffs

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_spinoffs.1.txt
    :language: text

结果解读：估值价格、依据和来源需要一起看；示意数值和文字不代表该证券的真实分拆条款。

:download:`下载完整示例 <../../../../example/corporate_actions.py>`
