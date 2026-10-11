==============
行业分类代码表
==============

各行业分类体系的全部节点。表格由 ``docs/_shared/generate_catalogs.py`` 从服务生成，反映的是\ **生成当天**\ 的
分类版本；分类体系会改版（申万 2021 年改版前后的节点数是 400 与 608），历史上的分类用 ``as_of`` 查：

..  code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="industry", source="SW")                      # 当前的申万分类
    >>> lf.all_instruments(type="industry", source="SW", as_of="2020-01-02")  # 改版前的申万分类
    >>> lf.instruments("480301.SW")                                           # 层级与上级节点

行业分类是什么、各体系有何不同，见 :doc:`../tutorials/classification`\ 。

怎么读
======

每个体系是一棵树，默认只展开一级行业；点击一行展开它的下一级，右上角的 ``+`` / ``−`` 一次展开或收起全部。
每行左边是行业代码（\ ``order_book_id``\ ，写法 ``<分类代码>.<分类体系>``\ ，可直接传给
:func:`~libfinance.get_industry_constituents`\ ），中间是名称，右边的数字是下一级的节点数。
缩进的深度就是层级（\ ``level``\ ，\ ``1`` 最粗），与 :func:`~libfinance.get_instrument_industry` 的 ``level`` 参数一致。

体系一览
========

..  list-table::
    :header-rows: 1
    :widths: 12 10 28 50

    *   - 体系
        - 市场
        - 层级
        - 说明
    *   - ``SW``
        - CN
        - 3 级：一级 / 二级 / 三级
        - 申万宏源研究的行业分类，A 股研究最常用；2021 版一级行业 31 个，Barra CNE5 的 31 个行业因子即申万一级
    *   - ``GICS``
        - US
        - 4 级：Sector / Industry Group / Industry / Sub-Industry
        - 全球行业分类标准，MSCI 与标普道琼斯联合制定，美股机构投资最常用
    *   - ``ICB``
        - US
        - 4 级：Industry / Supersector / Sector / Subsector
        - 富时罗素的行业分类基准
    *   - ``NAICS``
        - US
        - 5 级（2 位到 6 位代码）
        - 北美产业分类体系，政府统计口径，按生产活动划分
    *   - ``SIC``
        - US
        - 4 级：门类（字母）/ 大类 / 中类 / 小类
        - 美国标准产业分类，较老；SEC 登记文件仍使用它

申万（SW）
==========

名称为"—"的节点，是当前目录里服务尚未提供名称的节点（多为 2021 年改版前的旧代码），代码本身仍可查询。

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_sw.html

GICS
====

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_gics.html

ICB
===

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_icb.html

NAICS
=====

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_naics.html

SIC
===

.. raw:: html
    :file: ../../../_shared/tables/catalog_industry_sic.html
