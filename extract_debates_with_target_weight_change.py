
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from typing import Dict, Optional


def extract_target_id_from_filename(fname: str) -> Optional[str]:
    """Extract the target id from filename of form
    `<debateid>_T<k>of<n>_<targetid>.json`.

    Returns the target id string (e.g. '1563.2') or None if it cannot be
    parsed.
    """
    parts = fname.rsplit('_', 1)
    if len(parts) != 2:
        return None
    last = parts[1]
    if not last.endswith('.json'):
        return None
    return last[:-5]


def find_target_id_in_data(nodes: Dict[str, dict], edges: Dict[str, dict]) -> Optional[str]:
    """Fallback heuristic to infer a target id inside a sub-debate JSON.

    Heuristic used:
    - If there's only one node, that's the target.
    - Otherwise, count incoming edges per node and pick the node with the
      highest incoming count.
    - Returns None if nodes is empty.
    """
    if not nodes:
        return None
    if len(nodes) == 1:
        return next(iter(nodes.keys()))
    incoming = {nid: 0 for nid in nodes}
    for src, edge in edges.items():
        succ = edge.get('successor_id')
        if succ in incoming:
            incoming[succ] += 1
    # return the node with the highest incoming count
    target = max(incoming.items(), key=lambda kv: kv[1])[0]
    return target


def process_folder(input_folder: str, output_folder: str, verbose: bool = False) -> None:
    """Process all JSON files in input_folder and copy those with weight changes.

    Writes a `report.csv` in the output_folder with one row per processed file.
    """
    os.makedirs(output_folder, exist_ok=True)
    report_rows = []
    total = 0
    copied = 0

    for fname in sorted(os.listdir(input_folder)):
        if not fname.endswith('.json'):
            continue
        total += 1
        fpath = os.path.join(input_folder, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            reason = f'error_reading:{e}'
            report_rows.append((fname, None, None, None, 'skipped', reason))
            if verbose:
                print(f"Error reading {fpath}: {e}")
            continue

        nodes = data.get('nodes', {}) or {}
        edges = data.get('edges', {}) or {}

        target_id = extract_target_id_from_filename(fname)
        if target_id is None or target_id not in nodes:
            inferred = find_target_id_in_data(nodes, edges)
            if inferred is None:
                reason = 'no_target_found'
                report_rows.append((fname, None, None, None, 'skipped', reason))
                if verbose:
                    print(f"Could not determine target for file {fname}; skipping")
                continue
            target_id = inferred

        node = nodes.get(target_id)
        if node is None:
            reason = 'target_not_in_nodes'
            report_rows.append((fname, target_id, None, None, 'skipped', reason))
            if verbose:
                print(f"Target id {target_id} not found in {fname}; skipping")
            continue

        iw = node.get('initial_weight')
        fw = node.get('final_weight')
        if iw is None or fw is None:
            reason = 'missing_weight'
            report_rows.append((fname, target_id, iw, fw, 'skipped', reason))
            if verbose:
                print(f"Skipping {fname}: missing iw/fw for target {target_id}")
            continue

        if iw != fw:
            outpath = os.path.join(output_folder, fname)
            try:
                shutil.copy2(fpath, outpath)
                copied += 1
                reason = 'copied'
                report_rows.append((fname, target_id, iw, fw, 'copied', reason))
                if verbose:
                    print(f"Copied {fname} to {output_folder}")
            except Exception as e:
                reason = f'copy_failed:{e}'
                report_rows.append((fname, target_id, iw, fw, 'skipped', reason))
                if verbose:
                    print(f"Failed to copy {fname}: {e}")
        else:
            reason = 'no_change'
            report_rows.append((fname, target_id, iw, fw, 'skipped', reason))

    # write report CSV
    report_path = os.path.join(output_folder, 'report.csv')
    try:
        with open(report_path, 'w', newline='', encoding='utf-8') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(['filename', 'target_id', 'initial_weight', 'final_weight', 'action', 'reason'])
            for row in report_rows:
                writer.writerow(row)
        print(f"Wrote report to {report_path} ({copied}/{total} files copied)")
        # print a short preview
        for i, row in enumerate(report_rows[:50], 1):
            print(i, row)
    except Exception as e:
        print(f"Failed to write report: {e}")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Extract sub-debates with target weight change')
    p.add_argument('--input', '-i', default='sub-debates', help='Input folder containing sub-debate JSON files')
    p.add_argument('--output', '-o', default='debates_with_target_weight_change', help='Output folder to copy matched files')
    p.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    return p


def main_cli(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not os.path.isdir(args.input):
        print(f"Input folder does not exist: {args.input}")
        sys.exit(1)
    process_folder(args.input, args.output, verbose=args.verbose)


if __name__ == '__main__':
    main_cli()


