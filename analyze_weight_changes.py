#!/usr/bin/env python3
# analyze_weight_changes.py
# 

import json
import os
from typing import Dict, List, Tuple


def extract_target_id_from_filename(fname: str) -> str:
    """Extract the target id from filename of form
    `<debateid>_T<k>of<n>_<targetid>.json`.
    """
    parts = fname.rsplit('_', 1)
    if len(parts) != 2:
        return None
    last = parts[1]
    if not last.endswith('.json'):
        return None
    return last[:-5]


def analyze_weight_changes(input_folder: str = 'debates_with_target_weight_change') -> Dict:
    """Analyze weight changes in target arguments."""
    
    if not os.path.exists(input_folder):
        print(f"Error: Folder {input_folder} does not exist")
        return {}
    
    strengthening = []  # final > initial
    weakening = []      # final < initial
    no_change = []      # final = initial (shouldn't happen in this filtered set)
    errors = []         # processing errors
    
    total_files = 0
    
    for fname in sorted(os.listdir(input_folder)):
        if not fname.endswith('.json'):
            continue
            
        total_files += 1
        fpath = os.path.join(input_folder, fname)
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            errors.append((fname, f"read_error: {e}"))
            continue
        
        # Extract target ID from filename
        target_id = extract_target_id_from_filename(fname)
        if not target_id:
            errors.append((fname, "could_not_parse_target_id"))
            continue
            
        # Get nodes
        nodes = data.get('nodes', {})
        if target_id not in nodes:
            errors.append((fname, f"target_id_{target_id}_not_found"))
            continue
            
        # Get weights
        node = nodes[target_id]
        initial_weight = node.get('initial_weight')
        final_weight = node.get('final_weight')
        
        if initial_weight is None or final_weight is None:
            errors.append((fname, "missing_weights"))
            continue
            
        # Classify weight change
        weight_change = final_weight - initial_weight
        
        if weight_change > 0:
            strengthening.append((fname, target_id, initial_weight, final_weight, weight_change))
        elif weight_change < 0:
            weakening.append((fname, target_id, initial_weight, final_weight, weight_change))
        else:
            no_change.append((fname, target_id, initial_weight, final_weight, weight_change))
    
    # Print results
    print("\n" + "="*60)
    print("WEIGHT CHANGE ANALYSIS RESULTS")
    print("="*60)
    print(f"Total files processed: {total_files}")
    print(f"Successfully analyzed: {len(strengthening) + len(weakening) + len(no_change)}")
    print(f"Errors: {len(errors)}")
    print()
    
    print(f"🔼 STRENGTHENING (final > initial): {len(strengthening)}")
    print(f"🔽 WEAKENING (final < initial): {len(weakening)}")
    print(f"➡️  NO CHANGE (final = initial): {len(no_change)}")
    print()
    
    if len(strengthening) + len(weakening) > 0:
        total_with_change = len(strengthening) + len(weakening)
        strengthen_pct = (len(strengthening) / total_with_change) * 100
        weaken_pct = (len(weakening) / total_with_change) * 100
        
        print("PERCENTAGES:")
        print(f"Strengthening: {strengthen_pct:.1f}%")
        print(f"Weakening: {weaken_pct:.1f}%")
        print()
    
    # Show weight change statistics
    if strengthening:
        changes = [change for _, _, _, _, change in strengthening]
        print(f"Strengthening changes: min={min(changes):.4f}, max={max(changes):.4f}, avg={sum(changes)/len(changes):.4f}")
    
    if weakening:
        changes = [change for _, _, _, _, change in weakening]
        print(f"Weakening changes: min={min(changes):.4f}, max={max(changes):.4f}, avg={sum(changes)/len(changes):.4f}")
    
    # Show errors if any
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for fname, error in errors[:10]:  # Show first 10 errors
            print(f"  {fname}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    return {
        'total_files': total_files,
        'strengthening': len(strengthening),
        'weakening': len(weakening),
        'no_change': len(no_change),
        'errors': len(errors),
        'strengthening_details': strengthening,
        'weakening_details': weakening,
        'error_details': errors
    }


if __name__ == '__main__':
    results = analyze_weight_changes()