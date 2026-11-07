#!/usr/bin/env python3
"""Write the financial data dictionary tables: statement fields and financial metrics.

Two sources, each the one its data family generates and checks, so the dictionary is never edited by hand:

* statement fields -- financialstatement-release's ``docs/field-dictionary/<statement>.csv`` (written by its
  ``scripts/build_field_dictionary.py`` from the unified concept catalog), the fields
  :func:`get_pit_financials_ex` accepts;
* financial metrics -- financialmetrics' ``docs/data-dictionary.md``, the tables between the
  ``metrics:begin`` / ``metrics:end`` markers (checked there against ``formulas.json``), the fields
  :func:`get_financial_metrics` accepts.

Output: reStructuredText list-tables under ``docs/_shared/tables/financials/`` that both documentation trees
include. The English tables keep the Chinese notes and metric names, as the factor dictionary does.

Usage (from the repository root)::

    python docs/_shared/generate_financial_dictionary.py \\
        --statements ../financialstatement-release/docs/field-dictionary \\
        --metrics ../financialmetrics/docs/data-dictionary.md
    python docs/_shared/generate_financial_dictionary.py --statements ... --metrics ... --check   # stale -> exit 1
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys

from generate_factor_dictionary import literal, prose as _prose

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "_shared" / "tables" / "financials"

#: statement tables in order: income statement, balance sheet, cash flow statement
STATEMENTS = ["income_statement", "balance_sheet", "cash_flow_statement"]
#: metric categories in order
CATEGORIES = ["valuation", "operating", "cashflow", "financial", "growth"]

STATEMENT_HEADERS = {
    "zh": ["字段", "中文名", "期间", "单位", "行业", "市场", "释义、备注"],
    "en": ["Field", "Name", "Period", "Unit", "Industry", "Market", "Notes (zh)"],
}
METRIC_HEADERS = {
    "zh": ["字段", "中文名", "期间", "公式", "说明", "来源"],
    "en": ["Field", "Name (zh)", "Period", "Formula", "Notes (zh)", "Source"],
}
PERIOD = {"zh": {"instant": "时点", "duration": "期间"}, "en": {"instant": "instant", "duration": "duration"}}
UNIT = {
    "zh": {"monetary": "元（报告币种）", "per_share": "元/股", "shares": "股"},
    "en": {"monetary": "reporting currency", "per_share": "per share", "shares": "shares"},
}
INDUSTRY = {
    "zh": {"general": "一般", "bank": "银行", "insurance": "保险", "broker": "证券", "all": "全部"},
    "en": {"general": "general", "bank": "bank", "insurance": "insurance", "broker": "broker", "all": "all"},
}
METRIC_PERIOD_EN = {"日频": "daily"}
#: each table sits in a collapsed dropdown titled with its name and field count, so the page opens short
TITLES = {
    "zh": {"income_statement": "利润表", "balance_sheet": "资产负债表", "cash_flow_statement": "现金流量表",
           "valuation": "估值", "operating": "经营", "cashflow": "现金流", "financial": "财务", "growth": "成长"},
    "en": {"income_statement": "Income statement", "balance_sheet": "Balance sheet",
           "cash_flow_statement": "Cash flow statement", "valuation": "Valuation", "operating": "Operating",
           "cashflow": "Cash flow", "financial": "Financial", "growth": "Growth"},
}
COUNT = {"zh": "{title}（{n} 个字段）", "en": "{title} ({n} fields)"}
SOURCE = {
    "zh": {"rqdata": "通用", "barra": "Barra 输入", "market": "行情 + 股本"},
    "en": {"rqdata": "standard", "barra": "Barra input", "market": "market data"},
}
#: data vendors are not named in the published docs: the sources' notes are scrubbed, and a table that still
#: names one fails the run
VENDOR_PHRASES = [("RQData 用于配平的供应商派生项", "用于配平的派生项"), ("RQData ", ""), ("RQData", "")]
VENDORS = re.compile(r"rqdata|ricequant|米筐|wind资讯|万得|lseg|refinitiv|bloomberg|factset", re.I)
METRIC_ROW = re.compile(r"^\| `(?P<field>[^`]+)` \| (?P<name>[^|]*) \| (?P<category>[^|]*) \| (?P<period>[^|]*) \| "
                        r"(?P<formula>`[^`]*`) \| (?P<meaning>[^|]*) \| (?P<source>[^|]*) \|$")


def prose(text: str) -> str:
    """``generate_factor_dictionary.prose`` without the dangling ``\\`` it leaves when text ends in a code span,
    and without vendor names."""
    for old, new in VENDOR_PHRASES:
        text = text.replace(old, new)
    out = _prose(text)
    return out[:-1] if out.endswith("``\\") else out


def statement_rows(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        out = list(csv.DictReader(f))
    if not out:
        raise SystemExit(f"{path}: no fields")
    return out


def metric_rows(path: pathlib.Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    begin, end = text.find("<!-- metrics:begin"), text.find("<!-- metrics:end")
    if begin < 0 or end < 0:
        raise SystemExit(f"{path}: no metrics:begin / metrics:end markers")
    out = []
    for line in text[begin:end].splitlines():
        if line.startswith("| `"):
            m = METRIC_ROW.match(line.strip())
            if not m:
                raise SystemExit(f"{path}: cannot read the row {line!r}")
            out.append({k: v.strip() for k, v in m.groupdict().items()})
    unknown = sorted({row["category"] for row in out} - set(CATEGORIES))
    if not out or unknown:
        raise SystemExit(f"{path}: empty metric table or unknown categories {unknown}")
    return out


def _list_table(header: str, title: str, widths: str, headers: list[str], rows: list[list[str]]) -> str:
    table = [".. list-table::", "   :header-rows: 1", f"   :widths: {widths}", ""]
    table.append("   * - " + "\n     - ".join(headers))
    for cells in rows:
        table.append("   * - " + "\n     - ".join(cell or "\\-" for cell in cells))
    body = "\n".join(table).splitlines()
    lines = [header, "", f".. dropdown:: {title}", "    :icon: table", ""]
    lines += ["    " + line if line else "" for line in body]
    return "\n".join(lines) + "\n"


def _title(name: str, count: int, language: str) -> str:
    return COUNT[language].format(title=TITLES[language][name], n=count)


def statement_table(name: str, items: list[dict], language: str) -> str:
    def industries(value):
        codes = value.split(";") if value else []
        if set(codes) == {"general", "bank", "insurance", "broker"}:
            codes = ["all"]
        return ("、" if language == "zh" else ", ").join(INDUSTRY[language][c] for c in codes)

    rows = [[literal(item["field"]), prose(item["label_zh" if language == "zh" else "label_en"]),
             PERIOD[language][item["period_type"]], UNIT[language][item["unit_kind"]], industries(item["industries"]),
             ("、" if language == "zh" else ", ").join(item["markets"].split(";")), prose(item["note"])]
            for item in items]
    header = (f".. Generated by docs/_shared/generate_financial_dictionary.py from financialstatement-release"
              f" docs/field-dictionary/{name}.csv -- do not edit.")
    return _list_table(header, _title(name, len(rows), language), "17 14 6 9 9 7 38", STATEMENT_HEADERS[language], rows)


def metric_table(category: str, items: list[dict], language: str) -> str:
    rows = [[literal(item["field"]), prose(item["name"]),
             item["period"] if language == "zh" else METRIC_PERIOD_EN.get(item["period"], item["period"]),
             literal(item["formula"]), prose(item["meaning"]), SOURCE[language].get(item["source"], item["source"])]
            for item in items if item["category"] == category]
    header = (f".. Generated by docs/_shared/generate_financial_dictionary.py from financialmetrics"
              f" docs/data-dictionary.md ({category}) -- do not edit.")
    return _list_table(header, _title(category, len(rows), language), "20 14 10 28 20 8", METRIC_HEADERS[language],
                       rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--statements", type=pathlib.Path, required=True,
                        help="financialstatement-release's docs/field-dictionary/ directory")
    parser.add_argument("--metrics", type=pathlib.Path, required=True, help="financialmetrics' docs/data-dictionary.md")
    parser.add_argument("--check", action="store_true", help="exit 1 when a written table is stale")
    args = parser.parse_args()
    tables = {}
    for name in STATEMENTS:
        items = statement_rows(args.statements / f"{name}.csv")
        for language in STATEMENT_HEADERS:
            tables[OUT / f"{name}.{language}.rst"] = statement_table(name, items, language)
        print(f"{name}: {len(items)} fields")
    metrics = metric_rows(args.metrics)
    for category in CATEGORIES:
        for language in METRIC_HEADERS:
            tables[OUT / f"metrics-{category}.{language}.rst"] = metric_table(category, metrics, language)
    print(f"metrics: {len(metrics)} fields")
    named = [str(path.relative_to(REPO)) for path, text in tables.items() if VENDORS.search(text)]
    if named:
        raise SystemExit("a table names a data vendor: " + ", ".join(named))
    stale = [path for path, text in tables.items()
             if not (path.exists() and path.read_text(encoding="utf-8") == text)]
    for path in stale:
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tables[path], encoding="utf-8")
        print(("stale: " if args.check else "wrote: ") + str(path.relative_to(REPO)))
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
