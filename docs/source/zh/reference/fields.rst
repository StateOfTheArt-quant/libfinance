========
字段字典
========

各接口返回的字段含义与单位。

行情
====

:func:`~libfinance.get_price` 返回的列：

..  list-table::
    :header-rows: 1
    :widths: 24 16 60

    *   - 字段
        - 单位
        - 含义
    *   - ``open`` / ``high`` / ``low`` / ``close``
        - 元
        - 开盘、最高、最低、收盘价。受 ``adjust_type`` 影响
    *   - ``volume``
        - 股
        - 成交量。\ **也受复权影响**\ （与价格反向缩放）
    *   - ``turnover``
        - 元
        - 成交额。不受复权影响
    *   - ``limit_up`` / ``limit_down``
        - 元
        - 涨停价、跌停价。美股为 ``NaN``

索引是 ``(order_book_id, datetime)``\ 。

证券主数据
==========

:func:`~libfinance.all_instruments` 返回的目录：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 代码，如 ``600000.XSHG``\ 、\ ``000300.XSHG``\ 、\ ``480000.SW``\ 、\ ``300008.THS``
    *   - ``type``
        - ``stock`` 股票 / ``index`` 指数 / ``industry`` 行业 / ``theme`` 主题
    *   - ``market``
        - ``CN`` / ``US``
    *   - ``name``
        - 名称，如 ``浦发银行``\ 、\ ``沪深300``\ 、\ ``银行``
    *   - ``exchange``
        - 上市交易所，仅股票有
    *   - ``source``
        - 给这个代码编号的机构：股票是交易所，指数是发布机构（\ ``CSI``\ 、\ ``SPDJI``……），
          行业是分类体系（\ ``SW``\ 、\ ``GICS``……），主题是 ``THS``

:func:`~libfinance.instruments` 返回的对象带更多属性，随类型不同；指数、行业、主题的属性见下文
`指数、行业与主题`_\ 。

股本
====

:func:`~libfinance.get_shares`\ ，\ **所有字段单位均为股**\ ：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``total``
        - 总股本
    *   - ``total_a``
        - A 股总股本
    *   - ``circulation_a``
        - A 股流通股本
    *   - ``non_circulation_a``
        - A 股非流通股本
    *   - ``free_circulation``
        - 自由流通股本
    *   - ``preferred_shares``
        - 优先股

公司行动
========

分红（\ :func:`~libfinance.get_dividends`\ ）：

..  list-table::
    :header-rows: 1
    :widths: 30 70

    *   - 字段
        - 含义
    *   - ``ex_date``
        - 除权除息日，价格跳空发生在这天
    *   - ``record_date``
        - 股权登记日
    *   - ``payable_date``
        - 派发日
    *   - ``declaration_date``
        - 公告日
    *   - ``cash_per_share``
        - 每股派现
    *   - ``bonus_per_share``
        - 每股送股
    *   - ``transfer_per_share``
        - 每股转增
    *   - ``dist_kind`` / ``marker``
        - 分配类型与标记
    *   - ``currency``
        - 币种

拆股（\ :func:`~libfinance.get_splits`\ ）：\ ``ratio_from`` / ``ratio_to`` 读作
"``ratio_from`` 股变成 ``ratio_to`` 股"。

分拆（\ :func:`~libfinance.get_spinoffs`\ ，仅美股）：\ ``valuation_price`` 是估算价，
必须连着 ``valuation_basis`` 与 ``valuation_source`` 一起看。

财务
====

:func:`~libfinance.get_pit_financials_ex` 除了你请求的财务字段外，还带两列：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``info_date``
        - 这一版的披露日期，必定 ``<= as_of``
    *   - ``if_adjusted``
        - ``0`` 原始披露值，\ ``1`` 修订值

可用的财务字段名与因子名由服务端提供，不同部署可能不同。

指数、行业与主题
================

三类对象的代码表见 :doc:`index_meta`\ 、\ :doc:`industry_meta`\ 、\ :doc:`theme_meta`\ ；
它们之间的区别见 :doc:`../tutorials/classification`\ 。

对象属性
--------

:func:`~libfinance.instruments` 对指数返回：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 属性
        - 含义
    *   - ``source``
        - 发布机构：\ ``CSI`` 中证指数、\ ``CNI`` 国证指数、\ ``SZSE`` 深交所、\ ``SPDJI`` 标普道琼斯、
          ``NASDAQ`` 纳斯达克、\ ``FTSE_RUSSELL`` 富时罗素
    *   - ``trading_code``
        - 代码去掉命名空间后的部分，如 ``000300``
    *   - ``base_date`` / ``base_value``
        - 基日与基点：指数从哪天、从多少点开始计算
    *   - ``established_date``
        - 正式发布日。此前的点位是回算的
    *   - ``terminated_date``
        - 终止日；仍在发布的为 ``None``
    *   - ``return_variant``
        - 收益口径：\ ``price`` 价格指数（分红不再投资）；\ ``unspecified`` 未登记
    *   - ``currency``
        - 计价币种；未登记为 ``None``
    *   - ``lifecycle_status``
        - ``active`` 仍在发布；\ ``unknown`` 未登记

对行业与主题返回：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 属性
        - 含义
    *   - ``source``
        - 行业为分类体系（\ ``SW``\ 、\ ``GICS``\ 、\ ``ICB``\ 、\ ``NAICS``\ 、\ ``SIC``\ ），主题为 ``THS``
    *   - ``source_raw_id``
        - 分类体系自己的编号，如 ``480000``
    *   - ``level``
        - 层级，\ ``1`` 最粗；主题没有层级，为 ``None``
    *   - ``parent_order_book_id``
        - 上一级节点；一级行业与主题为 ``None``
    *   - ``effective_from`` / ``effective_to``
        - 这个节点（这一版分类）的生效区间；仍有效的 ``effective_to`` 为 ``None``

归属查询
--------

:func:`~libfinance.get_instrument_industry`\ 、\ :func:`~libfinance.get_instrument_indices`\ 、
:func:`~libfinance.get_instrument_themes` 返回同一种表，每行是"一只证券属于一个对象"：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 你传入的证券
    *   - ``related_order_book_id``
        - 它所属的行业 / 指数 / 主题的代码，可以直接传给对应的 ``get_*_constituents``
    *   - ``source``
        - 分类体系 / 指数发布机构 / ``THS``
    *   - ``market``
        - ``CN`` / ``US``
    *   - ``level``
        - 行业层级；指数与主题为空

一只证券在\ **同一个分类体系的同一层级**\ 只有一行（行业互斥）；指数与主题可以有任意多行。

指数权重
--------

:func:`~libfinance.get_index_weights`\ ：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 成分证券
    *   - ``weight``
        - 权重，同一天内加总为 1
    *   - ``date``
        - 权重所在的日子：月末快照日；非快照日由快照漂移得到时为 ``as_of``
    *   - ``source``
        - 指数发布机构
    *   - ``basis``
        - 权重的来历：\ ``origin`` 由数据源直接发布；\ ``reconstructed`` 按指数编制方法重构。同一期不混用
    *   - ``methodology``
        - 权重的计算方式，见下表
    *   - ``quality_flags``
        - 已知的近似，列表；空列表表示没有已知近似。见下表

``methodology`` 的取值：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 取值
        - 含义
    *   - ``VENDOR_SNAPSHOT``
        - 指数公司或数据供应商发布的权重快照，原样使用
    *   - ``FREE_FLOAT_CAP``
        - 按自由流通市值加权重构
    *   - ``MODIFIED_CAP``
        - 按市值加权并施加单只成分的权重上限（如纳斯达克 100）
    *   - ``PRICE_WEIGHTED``
        - 按股价加权（如道琼斯工业平均）
    *   - ``FULL_CAP_PROXY``
        - 用总市值近似：真实指数按自由流通市值加权，但缺自由流通调整，只能用总股本代替

``quality_flags`` 的取值：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 取值
        - 含义
    *   - ``DRIFTED``
        - 非快照日：从最近一期快照按各成分复权收益率漂移得到（客户端计算）
    *   - ``NO_IWF``
        - 市值加权但用总股本代替了指数公司的自由流通调整（IWF）
    *   - ``SHARES_NOT_PIT``
        - 所用股本的可知时间未知或晚于快照日，不能证明当时已经知道
    *   - ``INCOMPLETE_MEMBERS``
        - 该期有不超过 5% 的成分缺输入，权重在其余成分上计算
    *   - ``CAP_AT_ANCHOR``
        - 权重上限在月末快照日施加，而不是指数实际的再平衡日
    *   - ``STALE_PRICE``
        - 快照日没有收盘价，用 7 天内最近一个收盘价
    *   - ``DELISTED_BEFORE_SNAPSHOT``
        - 快照里仍含几天前已退市的证券（指数公司在下一次审核才剔除）

带 ``NO_IWF``\ 、\ ``SHARES_NOT_PIT`` 的权重适合做近似基准，不适合做要求逐笔复现指数的跟踪。

行业与主题权重
--------------

:func:`~libfinance.get_industry_weights` 与 :func:`~libfinance.get_theme_weights`\ ：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 成分证券
    *   - ``weight``
        - 权重，加总为 1
    *   - ``methodology``
        - ``derived_equal_weight``\ ：由成分名单推出的等权。分类体系只给成分名单、不给权重，这不是供应商权重
    *   - ``source``
        - 分类体系 / ``THS``
    *   - ``effective_from`` / ``effective_to``
        - 这份成分名单的生效区间；仍有效的 ``effective_to`` 为 ``None``

实时行情
========

``Quote`` 的字段见 :doc:`../data/realtime`\ 。

因子
====

:func:`~libfinance.get_factor_exposure` 的列是因子全名，每个因子的公式与含义见 :doc:`factor_dictionary`\ 。
