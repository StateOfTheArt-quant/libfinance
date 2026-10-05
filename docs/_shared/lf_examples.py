"""``.. lf-examples:: <function>``: a function's examples, in Python and C++, with their real output.

Reads the snapshots ``update_examples.py`` writes (``_shared/examples/{python,cpp}.json``): for each
example a title, then one tab per language (Python first; the choice of language is kept across the
page and the site) with the code and what it printed. An example without a snapshot is left out with
a warning -- the page never shows code that has not run, or an error in place of output.
"""
from __future__ import annotations

import json
import os
import pathlib

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

STORE = pathlib.Path(__file__).resolve().parent / "examples"
REPO = pathlib.Path(__file__).resolve().parents[2]
LANGUAGES = (("python", "Python", "python"), ("cpp", "C++", "cpp"))
LABELS = {
    "zh": {"output": "输出", "note": "输出由 ``docs/_shared/update_examples.py`` 运行示例脚本生成：数据版本 ``{data}``，{date}。",
           "download": "下载示例脚本", "setup": "Python 用 ``import libfinance as lf``；C++ 用 ``namespace lf = libfinance;``，"
                                                   "``show()`` 等打印辅助见 ``docs/examples/cpp/show.hpp``。"},
    "en": {"output": "Output", "note": "Output produced by ``docs/_shared/update_examples.py`` running the example scripts: "
                                       "data version ``{data}``, {date}.",
           "download": "Download the example scripts", "setup": "Python uses ``import libfinance as lf``; C++ uses "
                                                                  "``namespace lf = libfinance;``, with ``show()`` and the other "
                                                                  "printing helpers in ``docs/examples/cpp/show.hpp``."},
}
logger = logging.getLogger(__name__)


def _load(name: str) -> dict:
    path = STORE / name
    return json.loads(path.read_text()) if path.exists() else {}


def _number(name: str) -> int:
    return int(name.rsplit(".", 1)[1])


def _indent(text: str, spaces: int) -> list[str]:
    pad = " " * spaces
    return [pad + line if line.strip() else "" for line in text.splitlines()]


class LibfinanceExamples(SphinxDirective):
    required_arguments = 1
    option_spec = {"setup": directives.flag}

    def run(self) -> list[nodes.Node]:
        function = self.arguments[0]
        lang = "en" if (self.config.language or "").startswith("en") else "zh"
        labels = LABELS[lang]
        snapshots = {key: _load(f"{key}.json") for key, _, _ in LANGUAGES}
        titles_en = _load("titles_en.json")
        for key, _, _ in LANGUAGES:
            self.env.note_dependency(str(STORE / f"{key}.json"))
        names = sorted({n for snap in snapshots.values() for n in snap if n.rsplit(".", 1)[0] == function}, key=_number)
        if not names:
            logger.warning(f"lf-examples: no snapshot for {function}; run docs/_shared/update_examples.py",
                           location=self.get_location())
            return []

        lines: list[str] = []
        if "setup" in self.options:
            lines += [labels["setup"], ""]
        scripts, dates, data = set(), set(), set()
        for index, name in enumerate(names, 1):
            present = [(key, tab, pyg) for key, tab, pyg in LANGUAGES if name in snapshots[key]]
            first = snapshots[present[0][0]][name]
            title = titles_en.get(name, first["title"]) if lang == "en" else first["title"]
            lines += [f".. rubric:: {index}. {title}", "   :class: lf-example-title", "",
                      ".. tab-set::", "   :sync-group: lang", "   :class: lf-example", ""]
            for key, tab, pygments in present:
                snap = snapshots[key][name]
                scripts.add(snap["script"])
                dates.add(snap.get("generated", ""))
                data.add((snap.get("data_version") or "")[:15])
                lines += [f"   .. tab-item:: {tab}", f"      :sync: {key}", "",
                          f"      .. code-block:: {pygments}", ""] + _indent(snap["code"], 9) + [""]
                lines += ["      .. code-block:: text", f"         :caption: {labels['output']}",
                          "         :class: lf-output", ""] + _indent(snap["output"], 9) + [""]
        downloads = []
        source_dir = pathlib.Path(self.env.doc2path(self.env.docname)).parent
        for script in sorted(scripts):
            relative = os.path.relpath(REPO / script, source_dir)
            downloads.append(f":download:`{pathlib.Path(script).name} <{relative}>`")
        lines += [".. container:: lf-example-note", "",
                  "   " + labels["note"].format(data=" / ".join(sorted(d for d in data if d)) or "?",
                                                date=" / ".join(sorted(d for d in dates if d)) or "?"),
                  "   " + labels["download"] + ": " + " · ".join(downloads), ""]
        container = nodes.container(classes=["lf-examples"])
        self.state.nested_parse(StringList(lines, source=f"<lf-examples {function}>"), self.content_offset, container)
        return [container]


#: Package internals that pages must not present to users: functions are called directly, the client
#: connects by itself (LIBFINANCE_HOST / LIBFINANCE_PORT), so there is no setup step to document.
INTERNAL_NAMES = ("init_client",)


def _check_internal_names(app, docname, source):
    for name in INTERNAL_NAMES:
        if name in source[0]:
            logger.warning(f"{name} is internal to the package and must not appear in the docs",
                           location=docname)


def setup(app):
    app.add_directive("lf-examples", LibfinanceExamples)
    app.connect("source-read", _check_internal_names)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
