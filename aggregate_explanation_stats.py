#!/usr/bin/env python3
# aggregate_explanation_stats.py
# 

import csv
import statistics
from pathlib import Path
from collections import defaultdict

# Directories
INPUT_DIR   = Path("size_explanation")  
OUTPUT_FILE = Path("aggregated_explanation_stats.csv")

# Metrics to aggregate 
METRICS   = ["pct_args_of_graph", "pct_branches_returned"]

# Bins: 0–10, 10–20, …, 90–100 
BIN_EDGES  = list(range(0, 101, 10))
BIN_LABELS = [f"bin_{low}_{low+10}" for low in BIN_EDGES[:-1]]

# Storage: { (explanation_type, ranking, metric) : [values] }
data = defaultdict(list)

print("=" * 60)
print("EXPLANATION STATISTICS AGGREGATION")
print("=" * 60)
print(f"Reading CSV files from: {INPUT_DIR}")
print(f"Output will be saved to: {OUTPUT_FILE}")

# Check if input directory exists
if not INPUT_DIR.exists():
    print(f"ERROR: Input directory '{INPUT_DIR}' not found")
    print(f"Current working directory: {Path.cwd()}")
    print("STOPPING EXECUTION to verify input directory path")
    exit(1)

# Count files for progress tracking
csv_files = list(INPUT_DIR.glob("*_size_analysis.csv"))
total_files = len(csv_files)

if total_files == 0:
    print(f"ERROR: No size analysis CSV files found in '{INPUT_DIR}'")
    print(f"Directory contents: {list(INPUT_DIR.iterdir()) if INPUT_DIR.exists() else 'Directory does not exist'}")
    print("STOPPING EXECUTION to verify file discovery")
    exit(1)

print(f"Found {total_files} size analysis files to process")
print("-" * 60)

# Read all CSV files 
processed_files = 0
for csv_file in csv_files:
    try:
        with csv_file.open("r", encoding="utf-8", newline="") as f:
            # Detect delimiter 
            sample = f.read(2048)
            delim  = "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","
            f.seek(0)
            
            reader = csv.DictReader(f, delimiter=delim)
            file_rows = 0
            
            for row in reader:
                etype = row.get("explanation_type", "")
                rank  = row.get("ranking", "")
                
                # Handle ranking format variations (underscores vs spaces)
                rank = rank.replace("_", " ") if rank else ""
                
                for metric in METRICS:
                    try:
                        val = float(row.get(metric, ""))
                        data[(etype, rank, metric)].append(val)
                        file_rows += 1
                    except (TypeError, ValueError):
                        print(f"ERROR: Corrupted or incomplete data in file {csv_file.name} (row: {row})")
                        print("STOPPING EXECUTION due to corrupted/incomplete file.")
                        exit(1)
            
            processed_files += 1
            
            # Progress update every 500 files
            if processed_files % 500 == 0:
                print(f"Progress: {processed_files}/{total_files} files processed")
                
    except Exception as e:
        print(f"ERROR: Failed to process file {csv_file.name}: {e}")
        print("STOPPING EXECUTION due to corrupted/incomplete file.")
        exit(1)

print(f"✓ Successfully processed {processed_files}/{total_files} files")
print(f"✓ Total data points collected: {sum(len(values) for values in data.values())}")

# Write aggregated CSV 
print("\nWriting aggregated statistics...")

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as outf:
    fieldnames = [
        "explanation_type", "ranking", "metric", "num_debates",
        "mean", "median", "std_dev"
    ] + BIN_LABELS
    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()

    # Sort keys for organized output
    sorted_keys = sorted(data.keys(), key=lambda x: (x[2], x[0], x[1]))  # Sort by metric, then type, then ranking
    
    for (etype, rank, metric), values in [(k, data[k]) for k in sorted_keys]:
        N       = len(values)
        mean_   = statistics.mean(values)   if N else 0.0
        median_ = statistics.median(values) if N else 0.0
        stddev_ = statistics.stdev(values)  if N > 1 else 0.0

        # Calculate bins 
        bins = {label: 0 for label in BIN_LABELS}
        for v in values:
            for i in range(len(BIN_EDGES) - 1):
                low, high = BIN_EDGES[i], BIN_EDGES[i+1]
                if (v == 100.0 and i == len(BIN_EDGES) - 2) or (low <= v < high):
                    bins[BIN_LABELS[i]] += 1
                    break

        # Console output (enhanced for better readability)
        print(f"→ {etype:<12} | {rank:<15} | {metric:<20} : {N:>5} debates | Mean: {mean_:>6.2f}% | Median: {median_:>6.2f}%")

        # Build output row 
        row = {
            "explanation_type": etype,
            "ranking":          rank,
            "metric":           metric,
            "num_debates":      N,  # Changed from num_graphs to num_debates
            "mean":             f"{mean_:.2f}",
            "median":           f"{median_:.2f}",
            "std_dev":          f"{stddev_:.2f}",
        }
        row.update(bins)
        writer.writerow(row)

print(f"\n✅ Aggregated statistics with bins written to {OUTPUT_FILE}")

# Summary statistics
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
unique_combinations = len(data)
total_data_points = sum(len(values) for values in data.values())
print(f"Unique combinations processed: {unique_combinations}")
print(f"Total data points: {total_data_points:,}")
print(f"Average data points per combination: {total_data_points/unique_combinations:.1f}")

# Show what combinations were found
explanation_types = set(k[0] for k in data.keys())
rankings = set(k[1] for k in data.keys())
metrics = set(k[2] for k in data.keys())

print(f"\nExplanation types found: {sorted(explanation_types)}")
print(f"Rankings found: {sorted(rankings)}")
print(f"Metrics analyzed: {sorted(metrics)}")
print(f"\nReady for statistical analysis and visualization!")