#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正中文 RST 的两类排版问题：行内标记的转义空格、标题下划线长度。

一、行内标记紧邻 CJK 字符

docutils 判断行内标记（``code``、**strong**、:role:`x`）的结束符时，要求它后面是空白
或一小撮 ASCII 标点。中文的全角标点（）。，不在那张表里，于是 ``"latest"``（默认）
这种写法会报 "Inline literal start-string without end-string"，标记原样漏到页面上。

RST 的标准解法是插入一个转义空格 ``\\ ``：它不产生任何输出，但让 docutils 认得边界。
本脚本把这件事批量做掉，并跳过代码块——那里的内容不参与行内解析，改了就是改内容。

用法::

    python _shared/fix_cjk_markup.py source/zh
"""
import pathlib
import re
import sys
import unicodedata

CJK = r"　-〿぀-ヿ一-鿿＀-￯"

# 行内标记（含角色），按从长到短匹配，避免 ** 被 * 抢先
INLINE = r"(?:``[^`\n]+``|:[a-z:]+:`[^`\n]+`|\*\*[^*\n]+\*\*)"

# 两条规则都对**完整构造**做匹配。只盯 ``**`` 这种标记本身是不行的：闭合的 ``**``
# 后面同样跟着中文标点，会被误当成一个开启标记，转义就插到了构造内部，把标记本身
# 拆坏——第一版正是这么错的。
_after = re.compile(r"(%s)(?=[%s])" % (INLINE, CJK))
_before = re.compile(r"(?<=[%s])(?=%s)" % (CJK, INLINE))

# 清理：把紧贴标记的转义空格先全部去掉，再重新按正确规则插入。这样脚本可以反复运行，
# 也能修好上一版插错的位置。
_strip_before = re.compile(r"\\ (?=(?:``|\*\*|:[a-z:]+:`))")
_strip_after = re.compile(r"(?:(?<=``)|(?<=\*\*))\\ ")


def _literal_line_flags(lines):
    """标出哪些行属于字面块（代码块 / :: 块），这些行不做替换。"""
    flags = [False] * len(lines)
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        starts_literal = (
            stripped.startswith(".. code-block::")
            or stripped.startswith(".. literalinclude::")
            or (stripped.endswith("::") and not stripped.startswith(".."))
        )
        if starts_literal:
            base = len(line) - len(line.lstrip())
            j = i + 1
            # 跳过指令选项与空行
            while j < len(lines) and (
                not lines[j].strip()
                or (len(lines[j]) - len(lines[j].lstrip())) > base
            ):
                flags[j] = True
                j += 1
            i = j
            continue
        i += 1
    return flags


def fix_text(text):
    lines = text.split("\n")
    literal = _literal_line_flags(lines)
    out = []
    for line, is_literal in zip(lines, literal):
        if is_literal:
            out.append(line)
            continue
        line = _strip_before.sub("", line)
        line = _strip_after.sub("", line)
        line = _after.sub(r"\1\\ ", line)
        line = _before.sub(r"\\ ", line)
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 标题下划线长度
# ---------------------------------------------------------------------------
#
# docutils 要求下划线**不短于标题的源文本**。两件事会让人算错长度：标题里写了行内
# 角色（``财务报表：:func:`...` `` 的源文本远长于它的显示宽度），以及中文字符按 1 个
# 字符计数却占 2 列。所以这里直接按源文本长度补齐，不靠肉眼对齐。

ADORNMENT = set(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")


def _column_width(text):
    """docutils 量的是**显示宽度**，不是字符数：中文字符占两列。

    所以 ``数据说明`` 这个标题要 8 个 ``=``，不是 4 个。照字符数补齐仍然会报
    "Title underline too short"。
    """
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def _is_adornment(line):
    s = line.rstrip()
    return len(s) >= 2 and s[0] in ADORNMENT and set(s) == {s[0]}


def fix_underlines(text):
    lines = text.split("\n")
    literal = _literal_line_flags(lines)
    for i, line in enumerate(lines):
        if literal[i] or not _is_adornment(line) or i == 0:
            continue
        title = lines[i - 1]
        if not title.strip() or _is_adornment(title):
            continue
        need = _column_width(title.rstrip())
        if _column_width(line.rstrip()) < need:
            lines[i] = line.rstrip()[0] * need
            # 有上划线的话一起补齐
            if i >= 2 and _is_adornment(lines[i - 2]):
                lines[i - 2] = lines[i - 2].rstrip()[0] * need
    return "\n".join(lines)


def main(roots):
    changed = 0
    for root in roots:
        for path in sorted(pathlib.Path(root).rglob("*.rst")):
            original = path.read_text(encoding="utf-8")
            fixed = fix_underlines(fix_text(original))
            if fixed != original:
                path.write_text(fixed, encoding="utf-8")
                changed += 1
                print("fixed", path)
    print("%d file(s) changed" % changed)


if __name__ == "__main__":
    main(sys.argv[1:] or ["source"])
