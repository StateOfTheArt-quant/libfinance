========
因子字典
========

每个因子的分组、公式、含义、回看窗口（lookback，交易日）与存储方式。表格由因子注册表生成，与
`factors-daybar 的 libraries/ <https://github.com/StateOfTheArt-quant/factors-daybar/tree/main/libraries>`_
保持一致；数据口径与计算方式见 :doc:`../data/factors`\ 。

读取时写全名：\ ``system/<库>/<因子>``\ ，如 ``system/qlib/KMID``\ 、\ ``system/barra-cne5/SIZE``\ 。
存储方式：\ **稠密**\ 为每个交易日一个值；\ **阶梯**\ 为只在变化时存储（财报、行业调整），读取时每个交易日都有值；
**截面**\ 为读取时在 ``universe`` 上计算，不存储。

qlib 与 Alpha158
================

``system/qlib`` 的 158 个量价因子。\ ``system/alpha158`` 按 Qlib Alpha158 的字段顺序引用这些因子，
因子名与数据相同（\ ``system/alpha158/KMID`` 即 ``system/qlib/KMID``\ ）。公式用 Qlib 表达式书写：
``$close`` 等为后复权价，\ ``Ref($close, 5)`` 为 5 个交易日前的值，\ ``Mean``\ 、\ ``Std``\ 、\ ``Corr`` 等为滚动统计。

..  include:: ../../../_shared/tables/factors/qlib.zh.rst

Barra CNE5
==========

``system/barra-cne5``\ ：风格因子是标准化之后的暴露（流通市值加权均值 0、等权标准差 1）；行业因子为申万 2021
一级行业的哑变量；COUNTRY 在截面中恒为 1。

..  include:: ../../../_shared/tables/factors/barra-cne5.zh.rst

Barra CNE5 描述符
=================

``system/barra-cne5-descriptor``\ ：未经截面处理的原始值。"分组"是描述符所属的风格因子。记号：\ *r* 为后复权收盘价的
日收益，\ *r_m* 为中证全指的日收益，ewm 为指数加权（权重 0.5^(距今天数 / 半衰期)，窗口截断）。

..  include:: ../../../_shared/tables/factors/barra-cne5-descriptor.zh.rst

Barra CNE6 描述符
=================

``system/barra-cne6-descriptor``\ ：记号同上。与 CNE5 定义相同的描述符是同一份数据。

..  include:: ../../../_shared/tables/factors/barra-cne6-descriptor.zh.rst
