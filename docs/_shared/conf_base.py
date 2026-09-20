# -*- coding: utf-8 -*-
"""两棵语言树共享的 Sphinx 设置。

``source/zh/conf.py`` 与 ``source/en/conf.py`` 只定义各自的 ``language`` 与标题，
其余 ``from conf_base import *``。主题模板、静态资源与数据字典放在 ``docs/_shared``
下共享一份 —— 复制两份的话，改了一边忘了另一边不会有任何迹象。
"""
import pathlib
import sys
from datetime import datetime

_SHARED = pathlib.Path(__file__).resolve().parent
_REPO = _SHARED.parent.parent

# 让 autodoc 能 import 到未安装的源码树
sys.path.insert(0, str(_REPO))

import libfinance  # noqa: E402

import pytorch_sphinx_theme  # noqa: E402

# -- 项目信息 ----------------------------------------------------------------

project = "libfinance"
author = "StateOfTheArt.Quant"
copyright = f"{datetime.now().year}, {author}"

version = libfinance.__version__
release = version

# -- 通用配置 ----------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.katex",
    "sphinx_copybutton",
    "sphinx_togglebutton",
    "sphinx_design",
]

source_suffix = ".rst"
master_doc = "index"
exclude_patterns = []
pygments_style = "sphinx"

katex_prerender = True

templates_path = [str(_SHARED / "_templates")]

# -- HTML --------------------------------------------------------------------

html_theme = "pytorch_sphinx_theme"
html_theme_path = [pytorch_sphinx_theme.get_html_theme_path()]
html_theme_options = {
    "collapse_navigation": False,
    "display_version": True,
    "logo_only": True,
    "navigation_with_keys": True,
}

html_static_path = [str(_SHARED / "_static")]
html_logo = str(_SHARED / "_static" / "img" / "libfinance_logo.svg")
html_favicon = html_logo

html_context = {
    "extra_css_files": ["_static/css/libfinance.css"],
}

html_last_updated_fmt = "%Y-%m-%d %H:%M"
html_permalinks = True
html_permalinks_icon = "#"
htmlhelp_basename = "libfinancedoc"

# -- autodoc -----------------------------------------------------------------

autodoc_inherit_docstrings = True
autoclass_content = "both"
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_attr_annotations = True
autosummary_generate = True

# -- intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# -- 内部链接检查 ------------------------------------------------------------
#
# nitpicky 打开，这样参考页里写错的交叉引用会在构建时暴露，而不是变成一个不会跳转
# 的纯文本。下面只豁免那些**确实无处可指**的目标：类型注解里出现的宽泛类型，以及
# 本项目自己不生成 API 页的内部类。
nitpicky = True
nitpick_ignore = [
    ("py:class", "optional"),
    ("py:class", "datetime.datetime"),
    ("py:class", "pandas.core.frame.DataFrame"),
    ("py:class", "libfinance.subscribe.md_protocol.LoginRsp"),
    ("py:class", "libfinance.subscribe.md_protocol.SubRsp"),
    ("py:class", "libfinance.subscribe.md_protocol.SubAllRsp"),
    ("py:class", "libfinance.subscribe.md_protocol.SourceDirEntry"),
]
