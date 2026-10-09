7 因子
========================================

.. currentmodule:: libfinance

日频因子由 factors-daybar 提供：qlib 与 alpha158 的价量因子，Barra CNE5 的风格、行业、国家因子与原始描述符。
因子名写**全名**：库 ``owner/library[@rev]``\ （展开为它的全部因子）或因子 ``owner/library/factor[@rev]``\ ，
可以混在一次请求里；没有简称。\ ``start_date`` 与 ``end_date`` 相同时就是当天的截面。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_factor_exposure`
      - 按代码、日期区间读取因子暴露
    * - :func:`~libfinance.list_factor_libraries`
      - 有哪些因子库、各自的版本和因子数
    * - :func:`~libfinance.list_factors`
      - 一个库里有哪些因子

几个库的区别：

.. list-table::
    :header-rows: 1
    :widths: 28 72

    * - 库
      - 内容
    * - ``system/qlib``\ 、\ ``system/alpha158``
      - qlib 的价量因子；alpha158 是 qlib Alpha158 的 158 个因子（引用 ``system/qlib`` 的同名因子）
    * - ``system/barra-cne5``
      - 10 个风格因子（SIZE、BETA、MOMENTUM、RESVOL、NLSIZE、BTOP、LIQUIDITY、EARNYILD、GROWTH、LEVERAGE）、
        31 个申万一级行业哑变量、COUNTRY。风格因子是截面标准化后的暴露（流通市值加权均值 0、等权标准差 1），
        与 RQData ``get_factor_exposure`` 同口径，读取时在 ``universe`` 上计算
    * - ``system/barra-cne5-descriptor``\ 、\ ``system/barra-cne6-descriptor``
      - Barra 原始描述符（LNCAP、BETA、STOM……），个股自身的时间序列，与 universe 无关

**免费层**：未登录时 ``get_factor_exposure`` 的 start_date 会被夹到"今天往前 1 年"，一次最多 300 个代码；
客户端在请求会被裁剪时给出警告。登录后不限。

get_factor_exposure — 按代码、日期区间读取因子暴露
------------------------------------------------------------

.. autofunction:: get_factor_exposure

**示例**

.. lf-examples:: get_factor_exposure

结果解读：两只都是大盘银行股，SIZE 约 +1.45、BETA 约 −2、BTOP 与 LEVERAGE 很高，行业只有 BANKS 为 1。
600000.XSHG 与 600519.XSHG 的 SIZE 相同：两者的 LNCAP 都超过全市场 3 倍标准差，缩尾到同一个上界后再标准化——
RQData 同样把最大的几只股票的 size 给成同一个值。传入 ``universe`` 后 SIZE 在这几只银行股里重新标准化
（于是变成负值），LNCAP 是时序因子，不变。

list_factor_libraries — 有哪些因子库
--------------------------------------------

.. autofunction:: list_factor_libraries

**示例**

.. lf-examples:: list_factor_libraries

list_factors — 一个库里有哪些因子
--------------------------------------------

.. autofunction:: list_factors

**示例**

.. lf-examples:: list_factors
