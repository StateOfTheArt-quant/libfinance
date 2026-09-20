#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每个公开接口在两棵文档树里都要有条目，英文树的签名不能落后于代码。

这条测试的由来：文档分成 ``docs/source/zh`` 与 ``docs/source/en`` 两棵**独立**的
源码树。中文树用 autodoc，与 docstring 单一来源，不可能漂移；英文树因为 docstring
是中文，只能手写 ``.. py:function::``——于是就有了一个没人看守的缺口：

    加了一个新接口，中文文档自动就有了，英文文档没有，而仓里没有任何东西会告诉你。
    改了一个参数名，中文文档自动跟上，英文文档里那个旧名字会一直挂着。

这和 ``test_rpc_contract.py`` 是同一类问题（两边各自演进，中间没有闸门），所以用
同样的办法：静态扫描 + 断言。不需要服务端。

**这条测试守得住什么、守不住什么**，说清楚以免误以为它管得更宽：

* 守得住：接口有没有被文档覆盖、英文参考页的参数名与代码是否一致。
* 守不住：散文。英文说明写错了、过时了，这里查不出来——那需要人读。
"""
import ast
import inspect
import pathlib
import re

import pytest

import libfinance

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ZH = _ROOT / "docs" / "source" / "zh"
_EN = _ROOT / "docs" / "source" / "en"

#: ``libfinance.__all__`` 里**不面向使用者**的条目，不要求文档覆盖。
#:
#: ``init_client`` 是部署期的入口：服务地址在生产环境里配好，使用者直接调取数函数
#: 就行，不需要也不应该在自己的代码里指定服务地址。它仍然导出（自建服务、测试、
#: CI 要用），只是不进用户文档。
_NOT_API = {"__version__", "init_client"}

#: 中文树用 autodoc 指令引用对象。
_AUTODOC = re.compile(
    r"^\s*\.\.\s+auto(?:function|class|exception|method)::\s*([\w.]+)", re.M
)
#: 英文树手写 domain 指令。捕获名字与括号里的签名。
_PY_DIRECTIVE = re.compile(
    r"^\s*\.\.\s+py:(?:function|class|exception|method)::\s*([\w.]+)\s*(\(.*?\))?\s*$",
    re.M,
)


def _public_api():
    names = sorted(set(libfinance.__all__) - _NOT_API)
    assert names, "libfinance.__all__ 是空的，扫描器失效了"
    return names


def _documented(root, pattern):
    """树里所有被文档指令引用到的名字（取最后一段，便于和裸名比对）。"""
    found = {}
    for path in sorted(root.rglob("*.rst")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            dotted = match.group(1)
            found.setdefault(dotted.rsplit(".", 1)[-1], []).append(
                (path.relative_to(_ROOT), match)
            )
    return found


def _declared_params(signature_text):
    """从 ``(a, b=1, *, c=2)`` 里取出参数名。"""
    if not signature_text:
        return []
    inner = signature_text.strip()[1:-1]
    if not inner.strip():
        return []
    try:
        tree = ast.parse("def _f{}: pass".format(signature_text))
    except SyntaxError:
        pytest.fail("无法解析文档里的签名: {!r}".format(signature_text))
    args = tree.body[0].args
    return [a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)]


def _real_params(func):
    """代码里的参数名。**/*args 与 **kwargs 不计入** —— 文档没有义务把兼容用的
    ``**kwargs`` 摊开写，那是实现细节。"""
    kinds = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return [
        name
        for name, p in inspect.signature(func).parameters.items()
        if p.kind not in kinds
    ]


def test_scanner_finds_something():
    """扫描器本身失效时要红，否则下面几条会变成永远通过的空断言。"""
    assert len(_public_api()) >= 20
    assert len(_documented(_ZH, _AUTODOC)) >= 20
    assert len(_documented(_EN, _PY_DIRECTIVE)) >= 20


def test_every_public_api_is_in_the_chinese_docs():
    documented = _documented(_ZH, _AUTODOC)
    missing = [n for n in _public_api() if n not in documented]
    assert not missing, "中文文档缺少这些接口: {}".format(missing)


def test_every_public_api_is_in_the_english_docs():
    documented = _documented(_EN, _PY_DIRECTIVE)
    missing = [n for n in _public_api() if n not in documented]
    assert not missing, (
        "英文文档缺少这些接口: {}。英文树是手写的，新增接口要同时补 "
        "docs/source/en/reference/ 下的条目。".format(missing)
    )


def test_english_signatures_match_the_code():
    """英文参考页的参数名必须与代码一致。

    英文树不能用 autodoc（docstring 是中文），签名只能手抄，而手抄的东西会过期。
    这里逐个比对参数名——改了参数名却忘了改英文文档，在这里会红。
    """
    documented = _documented(_EN, _PY_DIRECTIVE)
    problems = []
    for name in _public_api():
        func = getattr(libfinance, name, None)
        if not callable(func) or inspect.isclass(func):
            continue
        entries = documented.get(name)
        if not entries:
            continue  # 上一条测试负责报这个
        rel_path, match = entries[0]
        declared = _declared_params(match.group(2))
        real = _real_params(func)
        if declared != real:
            problems.append(
                "{}: 文档 {} 写的是 {}，代码是 {}".format(name, rel_path, declared, real)
            )
    assert not problems, "英文文档的签名与代码不一致:\n  " + "\n  ".join(problems)


def test_names_used_by_examples_are_documented():
    """``example/`` 里用到的接口都要在文档里查得到。

    例子是很多人真正的入口。例子里出现、文档里查不到的名字，等于把读者领到一条
    没有说明的路上。
    """
    used = set()
    for path in sorted((_ROOT / "example").rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "libfinance":
                used.update(alias.name for alias in node.names)
    assert used, "没有从 example/ 里扫到任何 import，扫描器失效了"

    zh = _documented(_ZH, _AUTODOC)
    en = _documented(_EN, _PY_DIRECTIVE)
    missing = sorted(n for n in used if n not in zh or n not in en)
    assert not missing, "example/ 用到但文档没覆盖的接口: {}".format(missing)
