指数与概念成分
========================================

.. currentmodule:: libfinance

get_index_weights 从完整指数代码推断市场；概念编号不是证券代码，概念查询仍保留 market。

指数用 ``index_code`` 查询，概念用目录中的 ``concept_id`` 查询。
指数的 ``date`` 是权重日期；概念的 ``as_of`` 是信息可见性截止日。详见 :doc:`../data/universe`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_index_weights`
      - 查询指数在指定交易日的成分股及权重
    * - :func:`~libfinance.get_concept_meta`
      - 发现可查询的概念名称和编号
    * - :func:`~libfinance.get_concept_weights`
      - 查询一个或多个概念在指定知识时点的成分权重

get_index_weights — 查询指数在指定交易日的成分股及权重
--------------------------------------------------------------------------

.. autofunction:: get_index_weights

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/index_component.py
    :language: python
    :start-after: # [get_index_weights.1]
    :end-before: # [/get_index_weights.1]
    :prepend: from libfinance import get_index_weights

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_index_weights.1.txt
    :language: text

.. literalinclude:: ../../../../example/index_component.py
    :language: python
    :start-after: # [get_index_weights.2]
    :end-before: # [/get_index_weights.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_index_weights.2.txt
    :language: text

.. literalinclude:: ../../../../example/index_component.py
    :language: python
    :start-after: # [get_index_weights.3]
    :end-before: # [/get_index_weights.3]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_index_weights.3.txt
    :language: text

.. literalinclude:: ../../../../example/index_component.py
    :language: python
    :start-after: # [get_index_weights.4]
    :end-before: # [/get_index_weights.4]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_index_weights.4.txt
    :language: text

结果解读：省略 date 取最新锚点；指定 date 返回该交易日权重。权重和对完整结果计算，不能只加总展示的前几行。

:download:`下载完整示例 <../../../../example/index_component.py>`

get_concept_meta — 发现可查询的概念名称和编号
----------------------------------------------------------------

.. autofunction:: get_concept_meta

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/3b_concept_components.py
    :language: python
    :start-after: # [get_concept_meta.1]
    :end-before: # [/get_concept_meta.1]
    :prepend: from libfinance import get_concept_meta

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_concept_meta.1.txt
    :language: text

.. literalinclude:: ../../../../example/3b_concept_components.py
    :language: python
    :start-after: # [get_concept_meta.2]
    :end-before: # [/get_concept_meta.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_concept_meta.2.txt
    :language: text

结果解读：DEMO01/DEMO02 是示意编号，不可直接用于查询；脚本从实际目录取得有效编号。fields 缩小返回列。

:download:`下载完整示例 <../../../../example/3b_concept_components.py>`

get_concept_weights — 查询一个或多个概念在指定知识时点的成分权重
--------------------------------------------------------------------------------------

.. autofunction:: get_concept_weights

**示例**

以下按顺序执行，代码后的打印内容为\ **输出示意**\ ：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/3b_concept_components.py
    :language: python
    :start-after: # [get_concept_weights.1]
    :end-before: # [/get_concept_weights.1]
    :prepend: from libfinance import get_concept_weights, get_concept_meta

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_concept_weights.1.txt
    :language: text

结果解读：三张表依次展示一个概念、两个概念和历史可见成分。示意中概念乙在截止日尚无可见记录，因此最后不出现。

:download:`下载完整示例 <../../../../example/3b_concept_components.py>`
