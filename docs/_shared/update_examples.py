#!/usr/bin/env python3
"""Run the reference pages' example scripts (docs/examples/) and record what each example printed.

The reference pages show, for every example, its code and its real output in Python and in C++. They
read them from snapshots this script writes (docs/_shared/examples/{python,cpp}.json), never from the
scripts directly, so a page always shows code together with the output that code produced:

* an example is updated only when it ran without error and printed something;
* an example that fails keeps its previous snapshot (code and output together), and is reported;
* an example removed from the scripts is removed from the snapshots.

Examples are marked the same way in both languages, with the same title::

    # [all_instruments.1] 目录全貌：按类型与市场计数            (docs/examples/python/02_instrument.py)
    ...
    # [/all_instruments.1]

    {  // [all_instruments.1] 目录全貌：按类型与市场计数         (docs/examples/cpp/02_instrument.cpp)
      ...
    }  // [/all_instruments.1]

Usage (from the repository root)::

    python docs/_shared/update_examples.py --host libfinance.tech --port 8080
    python docs/_shared/update_examples.py --cpp-docker <image with Arrow C++ and a compiler>
    python docs/_shared/update_examples.py --only python            # or: --only cpp

Exit status 1 when any example failed (the others are still written).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

REPO = pathlib.Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "docs" / "examples"   # the reference pages' own examples, not example/
STORE = REPO / "docs" / "_shared" / "examples"
# Real-time quotes are documented in prose only (no example scripts here); kept for safety.
SKIPPED: set = set()

PY_START = re.compile(r"^# \[(?P<name>[a-z_]+\.\d+)\] (?P<title>.+?)\s*$")
PY_END = re.compile(r"^# \[/(?P<name>[a-z_]+\.\d+)\]\s*$")
CPP_START = re.compile(r"^(?P<indent>\s*)\{\s*// \[(?P<name>[a-z_]+\.\d+)\] (?P<title>.+?)\s*$")
CPP_END = re.compile(r"^\s*\}\s*// \[/(?P<name>[a-z_]+\.\d+)\]\s*$")

BEGIN, FAILED = "\x1e", "\x15"


def scripts(lang: str) -> list[pathlib.Path]:
    suffix = ".py" if lang == "python" else ".cpp"
    return sorted(p for p in (EXAMPLES / lang).glob(f"[0-9][0-9]_*{suffix}") if p.stem not in SKIPPED)


def parse(path: pathlib.Path, lang: str) -> tuple[list[str], dict[str, dict]]:
    """The lines before the first example (Python's imports) and the examples, in file order."""
    start, end = (PY_START, PY_END) if lang == "python" else (CPP_START, CPP_END)
    lines = path.read_text().splitlines()
    preamble: list[str] = []
    found: dict[str, dict] = {}
    current = None
    for number, line in enumerate(lines):
        opened, closed = start.match(line), end.match(line)
        if opened:
            if current:
                raise SystemExit(f"{path}:{number + 1}: {opened['name']} opens inside {current['name']}")
            current = {"name": opened["name"], "title": opened["title"], "first": number, "body": []}
        elif closed:
            if not current or closed["name"] != current["name"]:
                raise SystemExit(f"{path}:{number + 1}: [/{closed['name']}] closes nothing")
            body = "\n".join(current["body"])
            code = textwrap.dedent(body).strip("\n")
            found[current["name"]] = {"title": current["title"], "code": code, "script": f"docs/examples/{lang}/{path.name}",
                                      "first": current["first"], "last": number}
            current = None
        elif current:
            current["body"].append(line)
        elif not found:
            preamble.append(line)
    if current:
        raise SystemExit(f"{path}: {current['name']} is never closed")
    return preamble, found


# ---------------------------------------------------------------- running

PY_RUNNER = r'''
import contextlib, io, json, sys, traceback
import pandas as pd
# one line per row, every column (like the C++ examples' show()); the pages scroll sideways
pd.set_option("display.width", 10000)
pd.set_option("display.max_columns", None)
# CJK names take two columns on screen; without this the columns after them drift
pd.set_option("display.unicode.east_asian_width", True)
spec = json.load(open(sys.argv[1]))
base = {"__name__": "__example__"}
exec(compile(spec["preamble"], spec["script"], "exec"), base)
results = {}
for name, code in spec["examples"]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, f"{spec['script']} [{name}]", "exec"), dict(base))   # each example on its own
        results[name] = {"ok": True, "output": out.getvalue()}
    except Exception as error:  # noqa: BLE001
        results[name] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
json.dump(results, open(sys.argv[2], "w"))
'''


def run_python(path: pathlib.Path, examples: dict, preamble: list[str], env: dict, timeout: int) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        spec, out = pathlib.Path(tmp, "spec.json"), pathlib.Path(tmp, "out.json")
        spec.write_text(json.dumps({"script": str(path), "preamble": "\n".join(preamble),
                                    "examples": [(name, e["code"]) for name, e in examples.items()]}))
        runner = pathlib.Path(tmp, "runner.py")
        runner.write_text(PY_RUNNER)
        try:
            done = subprocess.run([sys.executable, str(runner), str(spec), str(out)], env=env,
                                  capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {name: {"ok": False, "error": f"timed out after {timeout}s"} for name in examples}
        if done.returncode != 0 or not out.exists():
            why = (done.stderr.strip().splitlines() or ["the script did not run"])[-1]
            return {name: {"ok": False, "error": why} for name in examples}
        return json.loads(out.read_text())


def instrument_cpp(path: pathlib.Path) -> str:
    """The program with each example in its own try block, its output preceded by a marker."""
    out = []
    for line in path.read_text().splitlines():
        opened, closed = CPP_START.match(line), CPP_END.match(line)
        if opened:
            out.append(f'{opened["indent"]}{{ std::cout << "{BEGIN}{opened["name"]}\\n" << std::flush; try {{')
        elif closed:
            out.append('    } catch (const lf::RpcError& e) { std::cout << "' + FAILED +
                       '" << (e.kind().empty() ? "RpcError" : e.kind()) << ": " << e.what() << "\\n"; }'
                       ' catch (const std::exception& e) { std::cout << "' + FAILED + '" << e.what() << "\\n"; }'
                       ' std::cout << std::flush; }')
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def split_output(stdout: str, names) -> dict:
    results = {}
    for chunk in stdout.split(BEGIN)[1:]:
        name, _, text = chunk.partition("\n")
        if FAILED in text:
            results[name] = {"ok": False, "error": text.split(FAILED, 1)[1].strip()}
        else:
            results[name] = {"ok": True, "output": text}
    for name in names:
        results.setdefault(name, {"ok": False, "error": "the program ended before this example"})
    return results


def run_cpp(paths: list[pathlib.Path], parsed: dict, env: dict, docker: str | None, timeout: int) -> dict:
    """Build the instrumented examples against this repository's C++ client and run them."""
    results: dict = {}
    every = {name for path in paths for name in parsed[path]}
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copytree(EXAMPLES / "cpp", work / "examples", ignore=shutil.ignore_patterns("build*"))
        for path in paths:
            (work / "examples" / path.name).write_text(instrument_cpp(path))
        for stale in (work / "examples").glob("[0-9][0-9]_*.cpp"):
            if stale.stem in SKIPPED:
                stale.unlink()
        shutil.copytree(REPO, work / "libfinance", ignore=shutil.ignore_patterns(".git", "build*", "docs", "example"))
        script = ("set -e; cmake -S /work/examples -B /work/build -DCMAKE_BUILD_TYPE=Release "
                  "-DFETCHCONTENT_SOURCE_DIR_LIBFINANCE=/work/libfinance > /work/build.log 2>&1; "
                  "cmake --build /work/build -j 8 >> /work/build.log 2>&1; "
                  + "; ".join(f"/work/build/libfinance_{p.stem} > /work/{p.stem}.out 2> /work/{p.stem}.err || true"
                              for p in paths))
        if docker:
            command = ["docker", "run", "--rm", "--network", "host", "-u", f"{os.getuid()}:{os.getgid()}",
                       "-e", "HOME=/tmp", "-e", f"LIBFINANCE_HOST={env['LIBFINANCE_HOST']}",
                       "-e", f"LIBFINANCE_PORT={env['LIBFINANCE_PORT']}", "-v", f"{work}:/work",
                       "--entrypoint", "bash", docker, "-c", script]
        else:
            command = ["bash", "-c", script.replace("/work", str(work))]
        try:
            done = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {name: {"ok": False, "error": f"timed out after {timeout}s"} for name in every}
        log = work / "build.log"
        if done.returncode != 0:
            tail = log.read_text().splitlines()[-15:] if log.exists() else done.stderr.splitlines()[-15:]
            print("C++ build failed:\n  " + "\n  ".join(tail), file=sys.stderr)
            return {name: {"ok": False, "error": "the C++ examples did not build"} for name in every}
        for path in paths:
            out = work / f"{path.stem}.out"
            results.update(split_output(out.read_text() if out.exists() else "", parsed[path]))
    return results


# ---------------------------------------------------------------- snapshots

def server_info(env: dict) -> dict:
    """The server the examples ran against: its address, version and data version."""
    probe = ("import json, libfinance as lf; from libfinance.client import get_client; "
             "print(json.dumps(get_client().call('ping', {})))")
    try:
        done = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True, timeout=60)
        pong = json.loads(done.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001 -- the examples themselves will report the failure
        pong = {}
    return {"server": f"{env['LIBFINANCE_HOST']}:{env['LIBFINANCE_PORT']}", "server_version": pong.get("version"),
            "data_version": pong.get("data_version")}


def update(lang: str, parsed: dict, results: dict, info: dict, today: str) -> dict:
    path = STORE / f"{lang}.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    current = {name: e for examples in parsed.values() for name, e in examples.items()}
    new, report = {}, {"updated": [], "kept": [], "missing": [], "removed": sorted(set(old) - set(current))}
    for name, example in current.items():
        result = results.get(name, {"ok": False, "error": "not run"})
        output = result.get("output", "") if result.get("ok") else ""
        if output.strip():
            new[name] = {"title": example["title"], "code": example["code"], "output": output.rstrip("\n"),
                         "script": example["script"], "generated": today, **info}
            report["updated"].append(name)
        elif name in old:
            new[name] = old[name]
            report["kept"].append(f"{name}: {result.get('error') or 'printed nothing'}")
        else:
            report["missing"].append(f"{name}: {result.get('error') or 'printed nothing'}")
    STORE.mkdir(parents=True, exist_ok=True)
    order = lambda name: (name.rsplit(".", 1)[0], int(name.rsplit(".", 1)[1]))  # noqa: E731
    path.write_text(json.dumps({name: new[name] for name in sorted(new, key=order)}, ensure_ascii=False, indent=1) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--host", default=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"))
    parser.add_argument("--port", default=os.environ.get("LIBFINANCE_PORT", "8080"))
    parser.add_argument("--only", choices=["python", "cpp"])
    parser.add_argument("--cpp-docker", metavar="IMAGE",
                        help="build and run the C++ examples in this image (Arrow C++, cmake, a compiler)")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    env = dict(os.environ, LIBFINANCE_HOST=args.host, LIBFINANCE_PORT=str(args.port),
               PYTHONPATH=str(REPO / "python") + os.pathsep + os.environ.get("PYTHONPATH", ""))
    today = _dt.date.today().isoformat()
    info = server_info(env)
    print(f"server {info['server']} (version {info['server_version']}, data {info['data_version']})")

    parsed = {lang: {} for lang in ("python", "cpp")}
    preambles = {}
    for lang in parsed:
        for path in scripts(lang):
            preambles[path], parsed[lang][path] = parse(path, lang)
    titles = {lang: {n: e["title"] for ex in parsed[lang].values() for n, e in ex.items()} for lang in parsed}
    for name in sorted(set(titles["python"]) ^ set(titles["cpp"])):
        print(f"warning: {name} is in one language only", file=sys.stderr)
    for name in sorted(set(titles["python"]) & set(titles["cpp"])):
        if titles["python"][name] != titles["cpp"][name]:
            print(f"warning: {name} has different titles: {titles['python'][name]!r} / {titles['cpp'][name]!r}",
                  file=sys.stderr)

    failed = False
    for lang in ("python", "cpp"):
        if args.only and args.only != lang:
            continue
        results: dict = {}
        if lang == "python":
            for path, examples in parsed[lang].items():
                results.update(run_python(path, examples, preambles[path], env, args.timeout))
        else:
            results = run_cpp(list(parsed[lang]), parsed[lang], env, args.cpp_docker, args.timeout)
        report = update(lang, parsed[lang], results, info, today)
        print(f"{lang}: {len(report['updated'])} updated, {len(report['kept'])} kept, "
              f"{len(report['missing'])} without a snapshot, {len(report['removed'])} removed")
        for key in ("kept", "missing", "removed"):
            for line in report[key]:
                print(f"  {key}: {line}")
        failed |= bool(report["kept"] or report["missing"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
