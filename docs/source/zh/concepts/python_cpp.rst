Python 与 C++ 统一的函数设计
====================================================================================================

研究多在 Python 里做，回测引擎、因子计算和实盘系统常在 C++ 里跑。
两边的数据接口只要在函数名、默认值或校验上差一点，策略从研究迁到生产时，
数字就会悄悄变掉，而且很难追查。libfinance 的 Python 与 C++ 客户端按同一份契约实现：
同一个函数，名称、参数顺序与默认值、校验与报错、返回的列都相同。

一份契约，两种实现
------------------------------

仓库里的 ``contract/contract.json`` 是两种客户端共同的依据。它列出全部 33 个公开函数，
每个函数写明：

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 项目
     - 约定的内容
   * - 名称与模块
     - ``get_price``\ 、\ ``all_instruments``\ ……两种语言同名
   * - 参数
     - 顺序、类型与默认值，例如 ``adjust_type`` 默认 ``"pre"``
   * - 返回
     - 表格的列与索引，或日期列表、对象
   * - 线上函数
     - 客户端实际调用的服务端函数，两种客户端发出同样的请求

客户端各自实现线上协议（帧、msgpack、LZ4），不依赖服务端的任何库；
两种客户端也共用仓库的版本号（\ ``VERSION``\ ），同一个版本号对应同一份契约。

同一次查询的两种写法
------------------------------

.. code-block:: python

   import libfinance as lf

   bars = lf.get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05", adjust_type="none")
   factors = lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158",
                                    "2026-09-07", "2026-09-10")

.. code-block:: cpp

   #include <libfinance/libfinance.hpp>
   namespace lf = libfinance;

   lf::Table bars = lf::get_price({"600000.XSHG", "AAPL.US"}, "2024-03-01", "2024-03-05",
                                  "1d", {}, false, true, "none");
   lf::Table factors = lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"}, "system/alpha158",
                                               "2026-09-07", "2026-09-10");

C++ 没有关键字参数，按契约里的参数顺序传；省略的参数取同样的默认值。

类型如何对应
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Python
     - C++
   * - 日期：\ ``str``\ 、\ ``date``\ 、\ ``int``
     - ``DateLike``\ ：\ ``"2024-03-01"``\ 、\ ``"20240301"``\ 、\ ``20240301``\ 、\ ``lf::Date``
   * - 一个代码或代码列表
     - ``Codes``\ ：\ ``"600000.XSHG"`` 或 ``{"600000.XSHG", "AAPL.US"}``
   * - ``None``
     - ``std::nullopt``\ ，或省略
   * - ``pandas.DataFrame``
     - ``arrow::Table``\ （\ ``lf::Table``\ ）；Python 的索引列在 C++ 里是普通列，列名相同
   * - ``ValueError``
     - ``std::invalid_argument``
   * - 服务端返回的错误
     - ``lf::RpcError``\ ：\ ``code()``\ 、\ ``message()``\ 、\ ``kind()``

有两处形式上的差别是有意保留的：单个代码调用 ``instruments`` 时，Python 返回一个对象或
``None``\ ，C++ 总是返回列表；Python 的告警走 ``warnings``\ ，C++ 走 ``lf::set_warning_handler``\ 。

如何保证一致
------------------------------

契约写下来不等于实现一致，所以仓库里另有一套核对：\ ``contract/conformance/`` 把同一组调用
分别经 Python 客户端和 C++ 客户端发给同一个服务端，逐项比对答案——表格按列名与行，
日期按 ISO 日，数值按 1e-9 相对误差，错误按类别与消息，告警按列表。用例包括正常查询，
也包括参数错误、越界日期和未知代码，因为报错是否一致与结果是否一致同样重要。
另有一项检查确认 C++ 实现的函数清单与契约完全相同。

C++ 客户端的安装与使用见
`cpp/README.md <https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/README.md>`_\ 。
