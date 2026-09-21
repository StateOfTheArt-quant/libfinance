行业分类
========================================

.. currentmodule:: libfinance

get_instrument_industry 按证券代码推断市场；按行业代码查询与行业目录仍可指定 market。

支持申万分类 ``source="sw"``\ ，按 ``level=1/2/3`` 选择层级。
历史股票池需要让分类表、行业归属和成分查询使用同一个 ``date``\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_industry_mapping`
      - 发现行业代码、名称与分类层级
    * - :func:`~libfinance.get_instrument_industry`
      - 查询股票在指定日期属于哪个行业
    * - :func:`~libfinance.get_industry`
      - 反向查询某行业包含哪些股票

get_industry_mapping — 发现行业代码、名称与分类层级
--------------------------------------------------------------------------

.. autofunction:: get_industry_mapping

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/3a_industry.py
    :language: python
    :start-after: # [get_industry_mapping.1]
    :end-before: # [/get_industry_mapping.1]
    :prepend: from libfinance import get_industry_mapping

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_industry_mapping.1.txt
    :language: text

.. literalinclude:: ../../../../example/3a_industry.py
    :language: python
    :start-after: # [get_industry_mapping.2]
    :end-before: # [/get_industry_mapping.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_industry_mapping.2.txt
    :language: text

结果解读：同一来源的新旧分类表可以相同，也可能随分类调整变化；一级到三级字段用于定位层级。

:download:`下载完整示例 <../../../../example/3a_industry.py>`

get_instrument_industry — 查询股票在指定日期属于哪个行业
----------------------------------------------------------------------------------

.. autofunction:: get_instrument_industry

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/3a_industry.py
    :language: python
    :start-after: # [get_instrument_industry.1]
    :end-before: # [/get_instrument_industry.1]
    :prepend: from libfinance import get_instrument_industry

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_instrument_industry.1.txt
    :language: text

结果解读：循环依次打印一级和三级分类，代码与名称字段随 level 改变；示意省略其他列。

:download:`下载完整示例 <../../../../example/3a_industry.py>`

get_industry — 反向查询某行业包含哪些股票
--------------------------------------------------------

.. autofunction:: get_industry

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/3a_industry.py
    :language: python
    :start-after: # [get_industry.1]
    :end-before: # [/get_industry.1]
    :prepend: from libfinance import get_industry, get_industry_mapping

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_industry.1.txt
    :language: text

结果解读：两行分别对应历史与最新成分列表；成员可能变化。证券代码占位仅用于展示形状。

:download:`下载完整示例 <../../../../example/3a_industry.py>`
