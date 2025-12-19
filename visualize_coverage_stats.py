#!/usr/bin/env python3
# visualize_coverage_stats.py

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 1) Update this path to the location of the aggregated CSV
CSV_PATH = "aggregated_explanation_stats.csv"

# 2) Output directory for the plots
OUTPUT_DIR = "coverage_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3) Read the CSV 
df = pd.read_csv(CSV_PATH, sep=None, engine="python")

# 4) Add a combined label column for plotting
df["group"] = df["explanation_type"] + " | " + df["ranking"]

# 5) Plot mean ± std_dev bar charts
for metric_name, title_suffix in [
    ("pct_args_of_graph", "Arguments"),
    ("pct_branches_returned", "Branches"),
]:
    sub = df[df["metric"] == metric_name].copy()
    x = np.arange(len(sub))
    means   = sub["mean"].astype(float).values
    stddevs = sub["std_dev"].astype(float).values
    labels  = sub["group"].tolist()

    plt.figure(figsize=(10, 6))
    plt.bar(x, means, yerr=stddevs, capsize=6, color="C0", alpha=0.8)
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel("Coverage (%)")
    plt.title(f"Mean ± Std Dev of Coverage – {title_suffix}")
    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, f"mean_std_{metric_name}.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved {out_file}")

# 6) Plot stacked bar charts of bins
bin_cols = [c for c in df.columns if c.startswith("bin_")]
# Define colors matching the legend
bin_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

for metric_name, title_suffix in [
    ("pct_args_of_graph", "Arguments"),
    ("pct_branches_returned", "Branches"),
]:
    sub = df[df["metric"] == metric_name].copy()
    x = np.arange(len(sub))
    labels = sub["group"].tolist()

    plt.figure(figsize=(10, 6))
    bottom = np.zeros(len(sub))
    for i, bin_col in enumerate(bin_cols):
        vals = sub[bin_col].astype(int).values
        color = bin_colors[i] if i < len(bin_colors) else f'C{i}'
        plt.bar(x, vals, bottom=bottom, label=bin_col, width=0.8, color=color)
        bottom += vals

    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel("Number of Graphs")
    plt.title(f"Coverage Bin Distribution – {title_suffix}")
    plt.legend(title="Bins", bbox_to_anchor=(1.03, 1), loc="upper left")
    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, f"bins_{metric_name}.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved {out_file}")

print("All plots generated!")