#!/usr/bin/env python3
"""Plot turnover_distribution for the 85k and 90k threshold datasets.

Produces:
  turnover_distribution_85k.png
  turnover_distribution_90k.png
  turnover_distribution_compare.png  (both overlaid)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATASETS = {85: "synthetic_firms_85k.csv", 90: "synthetic_firms_90k.csv"}
LO, HI = 60, 120
bins = np.arange(LO, HI + 1, 1.0)               # £1k bins
centers = (bins[:-1] + bins[1:]) / 2

def density(thr):
    d = pd.read_csv(DATASETS[thr])
    w = d["weight"] if "weight" in d.columns else None
    h, _ = np.histogram(d["annual_turnover_k"], bins=bins, weights=w)
    return h

dens = {}
for thr in DATASETS:
    h = density(thr)
    dens[thr] = h
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(centers, h, color="steelblue", lw=2)
    ax.axvline(thr, color="red", ls="--", lw=2, label=f"VAT Threshold (£{thr}k)")
    ax.set_xlabel("Turnover (£k)", fontsize=12)
    ax.set_ylabel("Number of Firms", fontsize=12)
    ax.set_title(f"Firm Turnover Distribution — £{thr}k threshold assumption", fontsize=13, fontweight="bold")
    ax.set_xlim(LO, HI); ax.grid(True, alpha=0.3); ax.legend(fontsize=11)
    plt.tight_layout()
    out = f"turnover_distribution_{thr}k.png"
    plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    print(f"saved {out}  (peak {h.max():.0f})")

# overlay comparison
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(centers, dens[85], color="darkorange", lw=2, label="85k threshold data")
ax.plot(centers, dens[90], color="steelblue", lw=2, label="90k threshold data")
ax.axvline(85, color="darkorange", ls=":", lw=1.5, alpha=0.7)
ax.axvline(90, color="steelblue", ls=":", lw=1.5, alpha=0.7)
ax.set_xlabel("Turnover (£k)", fontsize=12); ax.set_ylabel("Number of Firms", fontsize=12)
ax.set_title("Firm Turnover Distribution — 85k vs 90k threshold assumptions", fontsize=13, fontweight="bold")
ax.set_xlim(LO, HI); ax.grid(True, alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig("turnover_distribution_compare.png", dpi=150, bbox_inches="tight"); plt.close()
print("saved turnover_distribution_compare.png")
