行业分类
========================================

.. currentmodule:: libfinance

行业以 ``order_book_id``\ （\ ``<分类代码>.<分类体系>``\ ，如 ``801780.SW``\ 、``10.GICS``\ ）命名，规则与证券相同；
``source`` 是分类体系（\ ``SW``\ 、``GICS``\ ……），``level`` 是层级。三个函数都按 ``as_of`` 回答"那一天的事实"，
历史股票池要让行业归属、成分与权重使用同一个 ``as_of``\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_instrument_industry`
      - 查询证券在指定日期属于哪些行业
    * - :func:`~libfinance.get_industry_constituents`
      - 反向查询某行业在指定日期包含哪些证券
    * - :func:`~libfinance.get_industry_weights`
      - 查询某行业成分的权重（带 methodology）

get_instrument_industry — 查询证券在指定日期属于哪些行业
----------------------------------------------------------------------------------

.. autofunction:: get_instrument_industry

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/python/08_industry.py
    :language: python
    :start-after: # [get_instrument_industry.1]
    :end-before: # [/get_instrument_industry.1]
    :prepend: from libfinance import get_instrument_industry

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_instrument_industry.1.txt
    :language: text

结果解读：循环依次打印一级和三级行业；``related_order_book_id`` 是行业代码，可以直接传给
:func:`~libfinance.get_industry_constituents`\ 。

:download:`下载完整示例 <../../../../example/python/08_industry.py>`

get_industry_constituents — 反向查询某行业包含哪些证券
--------------------------------------------------------------------------

.. autofunction:: get_industry_constituents

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/python/08_industry.py
    :language: python
    :start-after: # [get_industry_constituents.1]
    :end-before: # [/get_industry_constituents.1]
    :prepend: from libfinance import get_industry_constituents, get_instrument_industry

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_industry_constituents.1.txt
    :language: text

结果解读：两行分别对应历史与最新成分列表；成员可能变化。证券代码占位仅用于展示形状。

:download:`下载完整示例 <../../../../example/python/08_industry.py>`

get_industry_weights — 查询某行业成分的权重
--------------------------------------------------------

.. autofunction:: get_industry_weights

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/python/08_industry.py
    :language: python
    :start-after: # [get_industry_weights.1]
    :end-before: # [/get_industry_weights.1]
    :prepend: from libfinance import get_industry_weights

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_industry_weights.1.txt
    :language: text

结果解读：每行一个成分证券；``methodology`` 说明权重的来源，没有供应商权重和明确方法时不生成。

:download:`下载完整示例 <../../../../example/python/08_industry.py>`
