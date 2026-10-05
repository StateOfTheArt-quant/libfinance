# 构建文档

中英文是两棵独立的源码树，各自构建：

```bash
$ cd docs
$ pip install -r requirements.txt
$ pip install -e ..                 # autodoc 要能 import 到本包

$ python -m sphinx -b html source/zh build/html/zh
$ python -m sphinx -b html source/en build/html/en
```

产物分别在 `build/html/zh` 与 `build/html/en`，用浏览器打开 `index.html` 即可。

## 目录

```
docs/
  _shared/            两棵树共用的东西
    conf_base.py        Sphinx 设置；两棵树的 conf.py 都 import 它
    _templates/         主题模板覆盖
    _static/            图片与 CSS
    tables/             数据表（指数代码表），两棵树各 include 一次
    fix_cjk_markup.py   中文排版修正脚本，见下
  source/zh/          中文树；API 参考用 autodoc，与 docstring 单一来源
  source/en/          英文树；API 参考手写（docstring 是中文，不能 autodoc）
```

## 写中文文档时跑一下这个

```bash
$ python _shared/fix_cjk_markup.py source/zh
```

中文 RST 有两个陷阱，肉眼很难发现：

1. **行内标记紧邻全角标点时不生效。** docutils 判断 ``code``、**strong** 的结束符
   时，要求后面是空白或一小撮 ASCII 标点，全角的 `（` `，` `。` 不在表里。于是
   ``"latest"``（默认）会报 "Inline literal start-string without end-string"，
   标记原样漏到页面上。修法是插入转义空格 `\ `。
2. **标题下划线按显示宽度算。** 中文字符占两列，`数据说明` 需要 8 个 `=` 而不是 4 个。
   标题里再写个 `:func:` 角色，长度就更难数了。

这个脚本把两件事一起修好，可以反复运行，不会重复插入。
跑完看一眼 diff：它在少数位置会改坏标记（例如把转义空格插进 `**…**` 的结束符之前、删掉两个相邻行内代码之间的分隔），
只保留它对你改动部分的修正。

## 示例与输出

参考页里每个函数的示例由 `.. lf-examples:: <函数>` 渲染：每个示例一个标题，Python / C++ 两个标签页（默认 Python，
整页同步），各自带代码与**实际运行的输出**。代码与输出来自 `_shared/examples/` 的快照，快照由脚本生成：

```bash
# 在仓库根目录；C++ 示例需要一个带 Arrow C++ 与编译器的环境（本机，或 --cpp-docker 指定镜像）
$ python docs/_shared/update_examples.py --host <服务地址> --port <端口> [--cpp-docker <镜像>]
```

- 参考页有自己的示例脚本 `docs/examples/python/NN_*.py` 与 `docs/examples/cpp/NN_*.cpp`（与仓库根目录的 `example/` 无关，
  那里是给用户的示例程序）。改示例只改这里：两种语言用同样的标记与标题
  （`# [函数.序号] 标题` / `{  // [函数.序号] 标题 ... }  // [/函数.序号]`），每个示例独立可运行。
- 运行失败的示例保留上一次成功的代码与输出（脚本会列出），页面不会出现报错或半截输出；脚本里删掉的示例从快照移除。
- 英文站的示例标题在 `_shared/examples/titles_en.json`。
- 实时行情（11、12）只有文字说明，不生成示例。
- 文档里不出现 `init_client`：用户直接调用函数即可，构建时出现会告警。

## 改了接口之后

`test/test_docs_contract.py` 会检查每个公开接口在两棵树里都有条目，并逐个比对英文树
手写签名里的参数名与代码是否一致。新增或改名接口后它会红，提示你补英文文档。

散文它管不了——那需要人读。
