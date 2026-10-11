#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从服务生成指数、行业、主题的代码表（数据字典），写到 ``tables/catalog_*``。

指数与主题是平表：中英文两棵树用 ``.. csv-table:: :file:`` 引用同一份 CSV，表头在各自页面上写，
所以 CSV 只有数据、没有表头行。列的顺序与页面上的 ``:header:`` 一一对应，改列要两边一起改。

行业是树：CSV（代码、名称、层级、上级）之外，再从 CSV 渲染一份可逐级展开的 HTML
（``catalog_industry_*.html``），页面用 ``.. raw:: html :file:`` 引用。HTML 里没有要翻译的文字。

不要手改这些文件：在仓库根目录运行

    python docs/_shared/generate_catalogs.py [--host <服务地址> --port <端口>]

只改了树的样式、不需要重新取数时，加 ``--render-only``：只从现有 CSV 重新渲染 HTML。

代码表是生成当天的**当前**目录。历史上的目录用 ``all_instruments(..., as_of=...)`` 查，
不要照抄这里的数字。
"""
import argparse
import csv
import html
import pathlib
from concurrent.futures import ThreadPoolExecutor

import libfinance as lf

_OUT = pathlib.Path(__file__).resolve().parent / "tables"

#: 行业分类体系，按页面上出现的顺序。
INDUSTRY_SOURCES = ["SW", "GICS", "ICB", "NAICS", "SIC"]


def _blank(value):
    return "" if value is None or value != value else value  # NaN != NaN


def _write(name, rows):
    path = _OUT / "catalog_{}.csv".format(name)
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(
            [[_blank(v) for v in row] for row in rows])
    print("{:<40} {:>5} rows".format(str(path.relative_to(_OUT.parent.parent.parent)), len(rows)))


def _details(order_book_ids):
    return {i.order_book_id: i for i in lf.instruments(list(order_book_ids))}


def _count(func, order_book_id):
    try:
        members = func(order_book_id)
    except lf.client.RpcError:
        return None
    return len(members) if members else None


def _counts(func, order_book_ids):
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(order_book_ids, pool.map(lambda i: _count(func, i), order_book_ids)))


def indices():
    catalog = lf.all_instruments(type="index")
    details = _details(catalog.order_book_id)
    counts = _counts(lf.get_index_constituents, list(details))
    order = {"CN": 0, "US": 1}
    items = sorted(details.values(), key=lambda i: (order.get(i.market, 9), i.source or "~", i.order_book_id))
    rows = [[i.order_book_id, i.name, i.market, i.source, i.base_date,
             "" if i.base_value is None else "{:g}".format(i.base_value), i.established_date,
             counts[i.order_book_id]] for i in items]
    _write("index", rows)
    # 有成分数据的指数单独成表：只有它们能拿来做基准与历史股票池。
    _write("index_constituents", [r for r in rows if r[-1] is not None])


def _tree(nodes):
    """按树的先序排列：父节点后面紧跟它的子节点。"""
    children = {}
    for node in nodes:
        children.setdefault(node.parent_order_book_id, []).append(node)
    for siblings in children.values():
        siblings.sort(key=lambda n: n.source_raw_id)
    ids = {n.order_book_id for n in nodes}
    roots = [n for n in nodes if n.parent_order_book_id not in ids]
    roots.sort(key=lambda n: (n.level, n.source_raw_id))
    out = []

    def walk(node):
        out.append(node)
        for child in children.get(node.order_book_id, []):
            walk(child)

    for root in roots:
        walk(root)
    return out


def industries():
    for source in INDUSTRY_SOURCES:
        catalog = lf.all_instruments(type="industry", source=source)
        nodes = _tree(list(_details(catalog.order_book_id).values()))
        # 服务端没有名称的节点写"—"。
        _write("industry_{}".format(source.lower()),
               [[n.order_book_id, n.name or "—", n.level, n.parent_order_book_id] for n in nodes])
    render_industries()


def _tree_html(rows):
    """先序排列的 (代码, 名称, 层级, 上级) → 嵌套的 <details>：只露出一级，点击逐级展开。"""
    children = {}
    for code, name, level, parent in rows:
        children.setdefault(parent, []).append((code, name))
    codes = {r[0] for r in rows}

    def node(code, name):
        label = '<code class="lf-tree-code">{}</code><span class="lf-tree-name">{}</span>'.format(
            html.escape(code), html.escape(name))
        kids = children.get(code, [])
        if not kids:
            return '<div class="lf-tree-leaf">{}</div>'.format(label)
        return '<details><summary>{}<span class="lf-tree-count">{}</span></summary>{}</details>'.format(
            label, len(kids), "".join(node(*k) for k in kids))

    toggle = ('<button type="button" onclick="this.closest(\'.lf-tree\').querySelectorAll(\'details\')'
              '.forEach(d => d.open = {})">{}</button>')
    roots = [(code, name) for code, name, _, parent in rows if parent not in codes]
    return ('<div class="lf-tree"><div class="lf-tree-tools">' + toggle.format("true", "+")
            + toggle.format("false", "&minus;") + "</div>" + "".join(node(*r) for r in roots) + "</div>\n")


def render_industries():
    for source in INDUSTRY_SOURCES:
        name = "industry_{}".format(source.lower())
        with (_OUT / "catalog_{}.csv".format(name)).open(encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        (_OUT / "catalog_{}.html".format(name)).write_text(_tree_html(rows), encoding="utf-8")


def themes():
    catalog = lf.all_instruments(type="theme")
    details = _details(catalog.order_book_id)
    counts = _counts(lf.get_theme_constituents, list(details))
    items = sorted(details.values(), key=lambda i: i.order_book_id)
    _write("theme_ths", [[i.order_book_id, i.name, counts[i.order_book_id], i.effective_from] for i in items])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--render-only", action="store_true", help="只从现有 CSV 重新渲染行业树")
    args = parser.parse_args()
    if args.render_only:
        render_industries()
        return
    if args.host:
        lf.init_client(args.host, args.port)
    indices()
    industries()
    themes()


if __name__ == "__main__":
    main()
