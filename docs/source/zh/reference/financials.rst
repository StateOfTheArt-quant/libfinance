财务报表与因子
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

季度区间决定查哪几期报告，\ ``as_of`` 决定当时已知哪些版本。
回测应设置 ``as_of``\ ；字段与因子名以所连接服务支持的目录为准。详见 :doc:`../data/fundamentals`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_pit_financials_ex`
      - 按季度查询财报，限制披露时点并查看修订版本
    * - :func:`~libfinance.get_factor`
      - 查询 TTM 等财务衍生因子

get_pit_financials_ex — 按季度查询财报，限制披露时点并查看修订版本
------------------------------------------------------------------------------------------

.. autofunction:: get_pit_financials_ex

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/2_financials.py
    :language: python
    :start-after: # [get_pit_financials_ex.1]
    :end-before: # [/get_pit_financials_ex.1]
    :prepend: from libfinance import get_pit_financials_ex

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.1.txt
    :language: text

.. literalinclude:: ../../../../example/2_financials.py
    :language: python
    :start-after: # [get_pit_financials_ex.2]
    :end-before: # [/get_pit_financials_ex.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.2.txt
    :language: text

.. literalinclude:: ../../../../example/2_financials.py
    :language: python
    :start-after: # [get_pit_financials_ex.3]
    :end-before: # [/get_pit_financials_ex.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_pit_financials_ex.3.txt
    :language: text

结果解读：示意中 2024q1 有三次披露。as_of 排除 2025 年版本；all 保留截止日前的两版，而 latest 只保留较新的一版。

:download:`下载完整示例 <../../../../example/2_financials.py>`

get_factor — 查询 TTM 等财务衍生因子
------------------------------------------------------

.. autofunction:: get_factor

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/2_financials.py
    :language: python
    :start-after: # [get_factor.1]
    :end-before: # [/get_factor.1]
    :prepend: from libfinance import get_factor

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_factor.1.txt
    :language: text

.. literalinclude:: ../../../../example/2_financials.py
    :language: python
    :start-after: # [get_factor.2]
    :end-before: # [/get_factor.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_factor.2.txt
    :language: text

结果解读：因子按季度返回。最新因子也可能受后续财报修订影响，所以历史比较要统一 as_of。

:download:`下载完整示例 <../../../../example/2_financials.py>`
