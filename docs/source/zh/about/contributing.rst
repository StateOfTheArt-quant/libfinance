========
参与贡献
========

代码仓库在 `GitHub <https://github.com/StateOfTheArt-quant/libfinance>`_\ 。

报告问题
========

提 issue 时请附上 :doc:`../howto/troubleshooting` 结尾那段信息（版本号、覆盖区间、
完整调用与完整报错），这样能少一轮来回。

本地开发
========

..  code-block:: bash

    $ git clone https://github.com/StateOfTheArt-quant/libfinance
    $ cd libfinance
    $ pip install -e .
    $ pytest test/

部分测试需要一个在跑的服务端，通过环境变量指定；没有服务端时这些测试会自动跳过：

..  code-block:: bash

    $ LIBFINANCE_TEST_HOST=127.0.0.1 LIBFINANCE_TEST_PORT=8080 pytest test/

构建文档
========

文档有中英两棵独立的源码树，各自构建：

..  code-block:: bash

    $ cd docs
    $ pip install -r requirements.txt
    $ python -m sphinx -b html source/zh build/html/zh
    $ python -m sphinx -b html source/en build/html/en

中文 RST 有两个排版陷阱：行内标记紧邻中文标点时 docutils 不认边界，
以及标题下划线按\ **显示宽度**\ 计算（中文字符占两列）。写完跑一下：

..  code-block:: bash

    $ python _shared/fix_cjk_markup.py source/zh

它会把转义空格和下划线长度一并修好，可以反复运行。

改了接口之后
============

``test/test_docs_contract.py`` 会检查每个公开接口在两棵文档树里都有对应条目，
并核对英文树里手写的签名与代码一致。新增接口后它会失败，提示你补文档。
