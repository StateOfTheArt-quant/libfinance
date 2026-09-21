合约信息
========================================

.. currentmodule:: libfinance

先用 ``all_instruments`` 确定研究范围，再用 ``instruments`` 解析具体代码。
``order_book_id`` 是代码，\ ``symbol`` 是名称；历史代码查询用 ``as_of`` 指定时点。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.all_instruments`
      - 筛选某市场、某类型或历史时点的合约范围
    * - :func:`~libfinance.instruments`
      - 按一个或多个代码查询详细身份，支持跨市场列表

all_instruments — 筛选某市场、某类型或历史时点的合约范围
--------------------------------------------------------------------------

.. autofunction:: all_instruments

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [all_instruments.1]
    :end-before: # [/all_instruments.1]
    :prepend: from libfinance import all_instruments

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.1.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [all_instruments.2]
    :end-before: # [/all_instruments.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.2.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [all_instruments.3]
    :end-before: # [/all_instruments.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.3.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [all_instruments.4]
    :end-before: # [/all_instruments.4]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.4.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [all_instruments.5]
    :end-before: # [/all_instruments.5]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.5.txt
    :language: text

结果解读：输出只展示部分行列。type 和 market 控制范围；as_of 改变身份快照，不保证所展示的证券一定发生变化。

:download:`下载完整示例 <../../../../example/0a_instrument.py>`

instruments — 按一个或多个代码查询详细身份，支持跨市场列表
------------------------------------------------------------------------

.. autofunction:: instruments

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [instruments.1]
    :end-before: # [/instruments.1]
    :prepend: from libfinance import instruments

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/instruments.1.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [instruments.2]
    :end-before: # [/instruments.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/instruments.2.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [instruments.3]
    :end-before: # [/instruments.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/instruments.3.txt
    :language: text

.. literalinclude:: ../../../../example/0a_instrument.py
    :language: python
    :start-after: # [instruments.4]
    :end-before: # [/instruments.4]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/instruments.4.txt
    :language: text

结果解读：字符串输入得到单个对象；列表输入按输入顺序返回对象列表。历史查询展示当时的代码和身份。

:download:`下载完整示例 <../../../../example/0a_instrument.py>`

Instrument — 合约对象
----------------------------------------

.. autoclass:: libfinance.api.instrument.Instrument
    :members:
