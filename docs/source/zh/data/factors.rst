========
因子数据
========

日频因子覆盖 A 股，按\ **库**\ 组织：qlib / Alpha158 的量价因子，Barra CNE5 的风格、行业与国家因子，
以及 Barra CNE5、CNE6 的原始描述符，经 :func:`~libfinance.get_factor_exposure` 读取。每个因子的公式与含义见 :doc:`../reference/factor_dictionary`\ 。

因子库
======

..  list-table::
    :header-rows: 1
    :widths: 30 10 60

    *   - 库
        - 因子数
        - 内容
    *   - ``system/qlib``
        - 158
        - Qlib Alpha158 的日频量价因子：K 线形态、价格、滚动统计（5、10、20、30、60 日窗口）。
          公式与 Qlib（\ ``qlib/contrib/data/loader.py``\ ）逐项相同
    *   - ``system/alpha158``
        - 158
        - 按 Qlib Alpha158 的字段顺序引用 ``system/qlib`` 的同名因子，不产生新数据。
          读取整个库时列的顺序与 Qlib 的 Alpha158 handler 一致
    *   - ``system/barra-cne5``
        - 42
        - Barra 中国股票模型 CNE5：10 个风格因子（SIZE、BETA、MOMENTUM、RESVOL、NLSIZE、BTOP、LIQUIDITY、
          EARNYILD、GROWTH、LEVERAGE）、31 个申万 2021 一级行业因子、1 个国家因子 COUNTRY
    *   - ``system/barra-cne5-descriptor``
        - 17
        - CNE5 的原始描述符（LNCAP、BETA、HSIGMA、RSTR、STOM……），未经截面标准化
    *   - ``system/barra-cne6-descriptor``
        - 36
        - CNE6 的原始描述符：在 CNE5 基础上增加质量、长期反转、季节性、短期反转、历史 alpha 与股息率；
          与 CNE5 定义相同的 16 个描述符是同一份数据

``system/barra-cne6`` 保留给 CNE6 的风格因子（尚未提供）。当前发布里这个名字下仍是改名前的 36 个描述符，
与 ``system/barra-cne6-descriptor`` 数据相同；请使用后者，不要依赖前者。

时序因子与截面因子
==================

因子按计算方式分两类，决定了它的值是否依赖"和谁比"：

..  list-table::
    :header-rows: 1
    :widths: 22 38 40

    *   - 类别
        - 包括
        - 性质
    *   - 时序因子
        - ``system/qlib``\ 、\ ``system/alpha158``\ 、全部描述符、Barra 行业因子
        - 每只证券只用自己的历史计算，值预先算好并存储，与同时查询了哪些证券无关
    *   - 截面因子
        - Barra 风格因子、COUNTRY
        - 值取决于截面里有哪些股票，读取时由服务端计算；\ ``universe`` 决定截面

截面因子的默认截面是\ **当天全部 A 股**\ （上交所、深交所、北交所）。传入 ``universe``\ （代码列表）时，
整条计算流程在这批股票上重做；请求的代码不在 ``universe`` 中时，其截面因子为 ``NaN``\ 。
只想要不依赖任何截面的原始值，读对应的描述符库。

Barra CNE5 风格因子的计算
-------------------------

1. 每个描述符在 3 倍标准差处缩尾，再标准化：流通市值加权均值为 0，等权标准差为 1；
2. 按 Barra CNE5 手册的权重对描述符加权合成；缺少分析师预期数据的描述符（EPFWD、EGRLF、EGRSF）的权重按比例
   分给同组其他描述符；
3. 正交化：RESVOL 对 BETA、SIZE 回归取残差，NLSIZE 取 SIZE³ 对 SIZE 的残差；
4. 再标准化一次。

返回的是标准化之后的暴露，与 RQData ``get_factor_exposure(..., model="v1")`` 的口径一致。
缩尾的结果是：市值最大的若干只股票 SIZE 相同（都落在同一个上界）。

输入与口径
==========

* **量价因子**\ （qlib / Alpha158）的输入是\ **后复权**\ 日线（开、高、低、收、量、均价）。停牌日没有行情，值为
  ``NaN``\ ；窗口按交易日计，窗口不满时为 ``NaN``\ 。
* **描述符**\ 的输入是后复权日线、中证全指（000985.XSHG）作为市场收益、总市值与换手率等日频指标，以及财报。
  财报按 point-in-time 取：交易日 *d* 只用 *d* 当天已经公告的报告（见 :doc:`point_in_time`\ ）。
* 只依赖财报的描述符只在公告日变化（"阶梯"），读取时每个交易日都有值。
* 财报从 2005 年起有数据；5 年增长类描述符大约从 2010 年起才有值，CNE6 的长期反转、季节性需要 5 年左右的历史。
* 值为 ``float32``\ 。\ ``NaN`` 表示该证券当天在截面中、但无法计算（停牌、上市不久、财报缺失）。

名称与版本
==========

因子名写全名，没有简称：

* 库：\ ``owner/library``\ ，如 ``system/barra-cne5``\ ，展开为库中全部因子，列的顺序就是库的顺序；
* 因子：\ ``owner/library/factor``\ ，如 ``system/barra-cne5/SIZE``\ ；
* 版本：在末尾加 ``@revision``\ ，如 ``system/barra-cne5/SIZE@v2.0.0``\ 。省略时读当前版本。

:func:`~libfinance.list_factors` 返回带版本的全名。库的版本按语义化版本递增：增加因子升次版本号，删除或
改变因子升主版本号。研究结果需要可复现时，在代码里写明版本。

覆盖范围
========

因子数据的截止日按市场给出（\ ``markets.CN.cutoff``\ ），可能早于行情的截止日。请求的区间超出覆盖范围时
直接报错，而不是返回较短的表：

..  code-block:: python

    >>> get_factor_exposure("600000.XSHG", "system/alpha158/KMID", "2026-09-16", "2026-09-23")
    RpcError(code=2001): system/alpha158/KMID covers 2000-01-04 to 2026-09-10 in the CN store,
    not 2026-09-16 to 2026-09-23

错误信息里给出的区间就是该因子当前的覆盖范围。

免费层
======

未登录时，\ ``start_date`` 会被夹到"今天往前 1 年"，一次最多 300 个代码；请求被裁剪时客户端给出警告。
