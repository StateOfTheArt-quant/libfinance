行业分类
========================================

.. currentmodule:: libfinance

行业以 ``order_book_id``\ （\ ``<分类代码>.<分类体系>``\ ，如 ``480000.SW``\ 、``10.GICS``\ ）命名，规则与证券相同；
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

.. lf-examples:: get_instrument_industry

结果解读：\ ``related_order_book_id`` 是行业代码，可以直接传给 :func:`~libfinance.get_industry_constituents`\ ；
第二个示例省略 ``source`` 与 ``level``\ ，返回全部分类体系、全部层级。

get_industry_constituents — 反向查询某行业包含哪些证券
--------------------------------------------------------------------------

.. autofunction:: get_industry_constituents

**示例**

.. lf-examples:: get_industry_constituents

结果解读：返回成分证券代码的列表；示例打印个数与前 5 个。成员随时间变化，省略 ``as_of`` 取已确认的最新日期。

get_industry_weights — 查询某行业成分的权重
--------------------------------------------------------

.. autofunction:: get_industry_weights

**示例**

.. lf-examples:: get_industry_weights

结果解读：每行一个成分证券；``methodology`` 说明权重的来源，没有供应商权重和明确方法时不生成。

