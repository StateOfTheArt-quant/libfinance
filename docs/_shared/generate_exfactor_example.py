"""Rebuild the synthetic teaching data and figure; no server or market feed needed.

Run with a Python environment containing matplotlib:
    MPLCONFIGDIR=/tmp/libfinance-matplotlib python docs/_shared/generate_exfactor_example.py
"""
from pathlib import Path
import csv
from fractions import Fraction as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "figures"
DAYS = ["D0", "D1", "D2", "D3", "D4", "D5"]
EVENTS = ["", "", "cash dividend: 1/share", "", "bonus: 10-for-10", ""]
RAW = list(map(F, ["10", "10", "9", "9.9", "4.95", "5.445"]))
# PRIOR_CLOSE convention: f_event = prior close / theoretical ex-price.
FACTORS = [F(1), F(1), F(10, 9), F(10, 9), F(20, 9), F(20, 9)]
POST = [p * f for p, f in zip(RAW, FACTORS)]
PRE = [p / FACTORS[-1] for p in POST]
assert POST[0] == RAW[0] and PRE[-1] == RAW[-1]
assert PRE[1] == PRE[2] and PRE[3] == PRE[4]
assert POST[1] == POST[2] and POST[3] == POST[4]
assert all(a / b == FACTORS[-1] for a, b in zip(POST, PRE))
OUT.mkdir(exist_ok=True)
with (OUT / "exfactor-example.csv").open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["day", "event", "raw", "cumulative_factor", "pre", "post"])
    for row in zip(DAYS, EVENTS, RAW, FACTORS, PRE, POST):
        writer.writerow([float(v) if isinstance(v, F) else v for v in row])
with (OUT / "exfactor-example.txt").open("w") as stream:
    stream.write("day      raw      F(t)       pre      post\n")
    for day, raw, factor, pre, post in zip(DAYS, RAW, FACTORS, PRE, POST):
        stream.write(f"{day:3} {float(raw):8.3f} {float(factor):9.6f} {float(pre):9.3f} {float(post):9.3f}\n")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "svg.hashsalt": "libfinance-exfactor"})
fig, axes = plt.subplots(2, 1, figsize=(10, 7.8), sharex=True,
                         gridspec_kw={"height_ratios": [1.3, 1]}, layout="constrained")
x = list(range(len(DAYS)))
colors = ["#64748b", "#007f86", "#b85418"]
for series, label, color, marker in zip(
        (RAW, PRE, POST), ("Unadjusted (none)", "Latest anchor (pre)", "Initial anchor (post)"),
        colors, ("o", "s", "^")):
    axes[0].plot(x, [float(v) for v in series], color=color, label=label,
                 marker=marker, linewidth=2.4)
axes[0].set_title("Same security, three price scales", loc="left", weight="bold")
axes[0].set_ylabel("Price per share")
axes[0].set_ylim(3.7, 14.2)
axes[0].legend(loc="upper left", ncol=1, frameon=False)
for day, label in ((2, "Cash: 1/share"), (4, "Bonus: 10-for-10")):
    for ax in axes:
        ax.axvline(day, color="#cbd5e1", linestyle=":", zorder=0)
    axes[0].text(day + .07, 13.65, label, fontsize=10, va="top")
raw_returns = [100 * float(RAW[i] / RAW[i-1] - 1) for i in range(1, 6)]
adj_returns = [100 * float(PRE[i] / PRE[i-1] - 1) for i in range(1, 6)]
axes[1].bar([i-.16 for i in x[1:]], raw_returns, width=.32, color=colors[0], label="Unadjusted return")
axes[1].bar([i+.16 for i in x[1:]], adj_returns, width=.32, color=colors[1], label="Adjusted return (pre = post)")
axes[1].set_title("Mechanical gaps disappear; market moves remain", loc="left", weight="bold")
axes[1].set_ylabel("One-period change (%)")
axes[1].set_ylim(-60, 25)
axes[1].axhline(0, color="#94a3b8", linewidth=.8)
axes[1].legend(loc="lower left", frameon=False)
axes[1].set_xticks(x, DAYS)
for ax in axes:
    ax.grid(axis="y", alpha=.15)
axes[1].set_xlabel("Synthetic teaching data; no tax, fees or dividend reinvestment model")
for suffix in ("svg", "png"):
    fig.savefig(OUT / f"exfactor-example.{suffix}", dpi=160, metadata={"Date": None} if suffix == "svg" else None)
plt.close(fig)
print((OUT / "exfactor-example.txt").read_text())
