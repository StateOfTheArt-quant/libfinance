合约信息
========================================

.. currentmodule:: libfinance

先用 ``all_instruments`` 确定研究范围，再用 ``instruments`` 解析具体代码。
``order_book_id`` 是代码，\ ``name`` 是名称。目录里有四种类型——股票（stock）、指数（index）、行业（industry）、主题（theme），\ ``type`` 选类型，\ ``source`` 是编号机构：股票是交易所，指数是发布机构，行业是分类体系（申万 SW；GICS、ICB、NAICS、SIC），主题是主题目录（同花顺 THS）。历史查询用 ``as_of`` 指定时点；股票、指数与申万行业有历史，美国行业分类与主题目前只有当前快照。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.all_instruments`
      - 按类型（股票、指数、行业、主题）、市场、编号机构或历史时点筛选证券
    * - :func:`~libfinance.instruments`
      - 按代码查询证券，一个列表可混合四种类型与中美市场

all_instruments — 按类型（股票、指数、行业、主题）、市场、编号机构或历史时点筛选证券
------------------------------------------------------------------------------------

.. autofunction:: all_instruments

**示例**

以下按顺序执行，代码后的打印内容取自 2026-10-01 的生产数据；数据更新后行数与内容会变化，省略号表示 pandas 未展示的列。

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.1]
    :end-before: # [/all_instruments.1]
    :prepend: from libfinance import all_instruments

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.1.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.2]
    :end-before: # [/all_instruments.2]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.2.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.3]
    :end-before: # [/all_instruments.3]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.3.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.4]
    :end-before: # [/all_instruments.4]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.4.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.5]
    :end-before: # [/all_instruments.5]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.5.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.6]
    :end-before: # [/all_instruments.6]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.6.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [all_instruments.7]
    :end-before: # [/all_instruments.7]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/all_instruments.7.txt
    :language: text

结果解读：四种类型的返回形状相同，type、market、source 只改变范围；as_of 改变身份快照（申万 2021 年改版前 400 个行业节点，改版后 608 个）。

:download:`下载完整示例 <../../../../example/python/02_instrument.py>`

instruments — 按代码查询证券，一个列表可混合四种类型与中美市场
------------------------------------------------------------------------

.. autofunction:: instruments

**示例**

以下按顺序执行，代码后的打印内容取自 2026-10-01 的生产数据；数据更新后行数与内容会变化，省略号表示 pandas 未展示的列。

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [instruments.1]
    :end-before: # [/instruments.1]
    :prepend: from libfinance import instruments

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/instruments.1.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [instruments.2]
    :end-before: # [/instruments.2]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/instruments.2.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [instruments.3]
    :end-before: # [/instruments.3]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/instruments.3.txt
    :language: text

.. literalinclude:: ../../../../example/python/02_instrument.py
    :language: python
    :start-after: # [instruments.4]
    :end-before: # [/instruments.4]

打印结果：

.. literalinclude:: ../../../_shared/example_outputs/instruments.4.txt
    :language: text

结果解读：类型由代码决定，字符串输入得到单个对象，列表输入按输入顺序返回对象列表。历史查询展示当时的代码和身份；早于某类型发布的 as_of 报 CoverageError。

:download:`下载完整示例 <../../../../example/python/02_instrument.py>`

Instrument — 合约对象
----------------------------------------

.. autoclass:: libfinance.api.instrument.Instrument
    :members:
