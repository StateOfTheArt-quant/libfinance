====
安装
====

``libfinance`` 是一个纯 Python 客户端，数据在服务端，所以安装本身很轻——装完还需要
:doc:`连接一个服务 <connect>` 才能取数。

要求 Python 3.7 或更高版本。

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
    $ pip install -e .

确认装好了
==========

装完先确认\ **能 import**\ ，这一步不需要连服务：

..  code-block:: python

    >>> import libfinance
    >>> libfinance.__version__
    '0.0.6'

如果这一步报 ``ModuleNotFoundError``\ ，说明依赖没装全，重新装一次即可；
``libfinance`` 依赖 ``pandas``\ 、\ ``numpy``\ 、\ ``lz4``\ 、\ ``msgpack``\ 、\ ``six``\ 、
``python-dateutil``\ ，都会由 pip 自动带上。

下一步：\ :doc:`connect`\ 。
