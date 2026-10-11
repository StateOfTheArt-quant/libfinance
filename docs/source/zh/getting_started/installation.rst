====
安装
====

数据在服务端，客户端只负责请求与解析，安装很轻。下面是 Python 客户端的安装；它依赖 ``pandas``\ 、
``numpy``\ 、\ ``pyarrow``\ 、\ ``lz4``\ 、\ ``msgpack``\ ，由 pip 自动安装。

..  tip::

    **使用 C++？**\ C++ 客户端与 Python 版函数一一对应，通过 CMake ``FetchContent`` 引入项目，依赖 Apache Arrow C++。
    安装、构建与示例见 `C++ 客户端说明 <https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/README.md>`_\ 。

用 pip 安装
===========

..  code-block:: bash

    $ pip install libfinance

从源码安装
==========

想跟进未发布的改动，或者要改代码：

..  code-block:: bash

    $ git clone https://github.com/StateOfTheArt-quant/libfinance
    $ cd libfinance
    $ pip install -e python

确认装好了
==========

装完先确认\ **能 import**\ ，这一步不需要连服务：

..  code-block:: python

    >>> import libfinance
    >>> libfinance.__version__        # 仓库的版本号，C++ 与 Python 客户端相同

这一步报 ``ModuleNotFoundError`` 时，说明依赖没有装全，重新执行一次安装即可。

下一步：\ :doc:`quickstart`\ 。
