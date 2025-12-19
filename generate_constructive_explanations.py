import os
import csv
import json
import pandas as pd
import networkx as nx
from typing import List, Dict, Tuple

def load_branch_rankings_data(csv_path: str) -> Dict:
    """Load branch rankings data from CSV file."""
    #breakpoint()  # Breakpoint 1: Start of CSV loading
    data = {
        'debate_id': '',
        't_id': '',
        'direction': '',
        'rankings': {}
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 9:  # Need all 9 columns
                    debate_id, t_id, direction, heuristic, category = row[0:5]
                    branches_abv, branches, ranking_abv, ranking = row[5:9]
                    
                    # Store basic info from first row
                    if not data['debate_id']:
                        data['debate_id'] = debate_id
                        data['t_id'] = t_id
                        data['direction'] = direction
                    
                    # Parse branch data
                    if heuristic not in data['rankings']:
                        data['rankings'][heuristic] = {}
                    
                    # Convert string representations back to lists (safer than eval)
                    import ast
                    try:
                        branches_abv_list = ast.literal_eval(branches_abv) if branches_abv else []
                        branches_list = ast.literal_eval(branches) if branches else []
                        ranking_abv_list = ast.literal_eval(ranking_abv) if ranking_abv else []
                        ranking_list = ast.literal_eval(ranking) if ranking else []
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing lists in {csv_path}: {e}")
                        continue
                    
                    data['rankings'][heuristic][category] = {
                        'branches_abv': branches_abv_list,
                        'branches': branches_list,
                        'ranking_abv': ranking_abv_list,
                        'ranking': ranking_list
                    }
    
    except Exception as e:
        print(f"Error loading rankings CSV {csv_path}: {e}")
        return {}
 
    return data

def load_debate_data(debate_file: str, debates_folder: str) -> Dict:
    """Load debate JSON data."""
    debate_path = os.path.join(debates_folder, debate_file)
    
    try:
        with open(debate_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading debate file {debate_path}: {e}")
        return {}

def create_restriction(debate_data: Dict, args_subset: List[str]) -> Dict:
    """Create restriction of argumentation framework to subset of arguments."""
    # breakpoint()  # Breakpoint 2: Creating restriction
    if not args_subset:
        return {'nodes': {}, 'edges': {}}
    
    # Filter nodes
    restricted_nodes = {arg_id: debate_data['nodes'][arg_id] 
                       for arg_id in args_subset 
                       if arg_id in debate_data['nodes']}
    
    # Filter edges - keep only edges between arguments in subset
    restricted_edges = {}
    for src_id, edge_data in debate_data['edges'].items():
        dst_id = edge_data.get('successor_id')
        if src_id in args_subset and dst_id in args_subset:
            restricted_edges[src_id] = edge_data
    
    return {'nodes': restricted_nodes, 'edges': restricted_edges}

def apply_qem_to_restriction(restricted_framework: Dict) -> Dict:
    """Apply QEM semantics to a restricted framework and return final weights."""
    # breakpoint()  # Breakpoint 3: Applying QEM semantics
    nodes = restricted_framework['nodes']
    edges = restricted_framework['edges']
    
    if not nodes:
        return {}
    
    # Initial weights
    w_init = pd.Series({nid: nd["initial_weight"] for nid, nd in nodes.items()})
    
    # Build support/attack dictionaries and graph
    sup, att, G = {}, {}, nx.DiGraph()
    
    for src_id, e in edges.items():
        dst_id, rel = e["successor_id"], e.get("relation", 0.0)
        G.add_edge(src_id, dst_id)
        
        if rel > 0:
            sup.setdefault(dst_id, []).append(src_id)
        elif rel < 0:
            att.setdefault(dst_id, []).append(src_id)
    
    # Handle case with no edges (isolated nodes)
    if not G.edges():
        return {nid: w_init[nid] for nid in nodes.keys()}
    
    try:
        topo = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # Handle cycles by using arbitrary order
        topo = list(nodes.keys())
    
    # Apply QEM
    final_acc = {}
    for n in topo:
        final_acc[n] = qem_accept(n, sup, att, final_acc, w_init)
    
    return final_acc

def qem_accept(n, sup, att, final_acc, w_init):
    """QEM acceptance function."""
    if n not in sup and n not in att:
        return w_init[n]
    
    e = calculate_energy(n, sup, att, final_acc)
    w0 = w_init[n]
    return w0 + (1 - w0) * h(e) if e > 0 else w0 - w0 * h(-e)

def calculate_energy(n, sup, att, final_acc):
    """Calculate energy for QEM."""
    return sum(final_acc.get(s, 0) for s in sup.get(n, [])) - \
           sum(final_acc.get(a, 0) for a in att.get(n, []))

def h(x):
    """Transformation function for QEM."""
    return (max(x, 0) ** 2) / (1 + max(x, 0) ** 2)

def get_branch_arguments(branches_data: List[List[str]]) -> List[str]:
    """Flatten list of branch argument lists into single list."""
    all_args = []
    for branch_args in branches_data:
        all_args.extend(branch_args)
    return all_args

def generate_constructive_explanation(rankings_data: Dict, debate_data: Dict, heuristic: str) -> Dict:
    """Generate constructive explanation for a specific heuristic."""
    #breakpoint()  # DEBUG: Start of constructive explanation generation
    target_id = rankings_data['t_id']
    direction = rankings_data['direction']
    
    # Check if target_id exists in debate data
    if target_id not in debate_data['nodes']:
        print(f"ERROR: Target '{target_id}' not found in debate nodes")
        print(f"Available nodes (first 10): {list(debate_data['nodes'].keys())[:10]}")
        print(f"Total nodes: {len(debate_data['nodes'])}")
        return {
            'success': False,
            'constructive_explanation_abv': [],
            'constructive_explanation_arg': []
        }
    
    w0_target = debate_data['nodes'][target_id]['initial_weight']
    
    heuristic_data = rankings_data['rankings'].get(heuristic, {})
    
    if direction == "strengthening":
        #breakpoint()  # DEBUG: Strengthening case - initial setup
        # Strengthening case: start with unweakened con-branches + target
        unweakened_con = heuristic_data.get('unweakened con-branches', {})
        pro_branches = heuristic_data.get('pro-branches', {})
        con_weakening = heuristic_data.get('con-weakening branches', {})
        
        # Initial framework: unweakened con-branches + target
        base_args = get_branch_arguments(unweakened_con.get('branches', []))
        current_args = base_args + [target_id]
        
        # Check initial condition
        #breakpoint()  # DEBUG: Check initial strengthening condition
        restriction = create_restriction(debate_data, current_args)
        final_weights = apply_qem_to_restriction(restriction)
        w1_target = final_weights.get(target_id, w0_target)
        
        if w1_target > w0_target:
            # Already satisfied with just unweakened con-branches
            return {
                'success': True,
                'constructive_explanation_abv': [unweakened_con.get('branches_abv', []), []],
                'constructive_explanation_arg': [base_args, []]
            }
        
        # Add pro-branches incrementally
        #breakpoint()  # DEBUG: Start adding pro-branches incrementally
        pro_ranking = pro_branches.get('ranking', [])
        pro_ranking_abv = pro_branches.get('ranking_abv', [])
        
        added_pro_args = []
        added_pro_abv = []
        
        for i, pro_branch_args in enumerate(pro_ranking):
            added_pro_args.extend(pro_branch_args)
            if i < len(pro_ranking_abv):  # Safety check
                added_pro_abv.append(pro_ranking_abv[i])
            
            current_args = base_args + added_pro_args + [target_id]
            #breakpoint()  # DEBUG: Check pro-branch addition effect
            restriction = create_restriction(debate_data, current_args)
            final_weights = apply_qem_to_restriction(restriction)
            w1_target = final_weights.get(target_id, w0_target)
            
            if w1_target > w0_target:
                return {
                    'success': True,
                    'constructive_explanation_abv': [unweakened_con.get('branches_abv', []), added_pro_abv],
                    'constructive_explanation_arg': [base_args, added_pro_args]
                }
        
        # All pro-branches added, try con-weakening branches
        #breakpoint()  # DEBUG: Start adding con-weakening branches
        con_weak_ranking = con_weakening.get('ranking', [])
        con_weak_ranking_abv = con_weakening.get('ranking_abv', [])
        
        added_con_weak_args = []
        added_con_weak_abv = []
        
        for i, con_weak_args in enumerate(con_weak_ranking):
            added_con_weak_args.extend(con_weak_args)
            if i < len(con_weak_ranking_abv):  # Safety check
                added_con_weak_abv.append(con_weak_ranking_abv[i])
            
            current_args = base_args + added_pro_args + added_con_weak_args + [target_id]
            restriction = create_restriction(debate_data, current_args)
            final_weights = apply_qem_to_restriction(restriction)
            w1_target = final_weights.get(target_id, w0_target)
            
            if w1_target > w0_target:
                return {
                    'success': True,
                    'constructive_explanation_abv': [
                        unweakened_con.get('branches_abv', []), 
                        added_pro_abv,
                        added_con_weak_abv
                    ],
                    'constructive_explanation_arg': [
                        base_args, 
                        added_pro_args,
                        added_con_weak_args
                    ]
                }
    
    else:  # weakening case
        #breakpoint()  # DEBUG: Weakening case - initial setup
        # Weakening case: start with unweakened pro-branches + target
        unweakened_pro = heuristic_data.get('unweakened pro-branches', {})
        con_branches = heuristic_data.get('con-branches', {})
        pro_weakening = heuristic_data.get('pro-weakening branches', {})
        
        # Initial framework: unweakened pro-branches + target
        base_args = get_branch_arguments(unweakened_pro.get('branches', []))
        current_args = base_args + [target_id]
        
        # Check initial condition
        #breakpoint()  # DEBUG: Check initial weakening condition
        restriction = create_restriction(debate_data, current_args)
        final_weights = apply_qem_to_restriction(restriction)
        w1_target = final_weights.get(target_id, w0_target)
        
        if w1_target < w0_target:
            # Already satisfied with just unweakened pro-branches
            return {
                'success': True,
                'constructive_explanation_abv': [unweakened_pro.get('branches_abv', []), []],
                'constructive_explanation_arg': [base_args, []]
            }
        
        # Add con-branches incrementally
        #breakpoint()  # DEBUG: Start adding con-branches incrementally
        con_ranking = con_branches.get('ranking', [])
        con_ranking_abv = con_branches.get('ranking_abv', [])
        
        added_con_args = []
        added_con_abv = []
        
        for i, con_branch_args in enumerate(con_ranking):
            added_con_args.extend(con_branch_args)
            if i < len(con_ranking_abv):  # Safety check
                added_con_abv.append(con_ranking_abv[i])
            
            current_args = base_args + added_con_args + [target_id]
            #breakpoint()  # DEBUG: Check con-branch addition effect
            restriction = create_restriction(debate_data, current_args)
            final_weights = apply_qem_to_restriction(restriction)
            w1_target = final_weights.get(target_id, w0_target)
            
            if w1_target < w0_target:
                return {
                    'success': True,
                    'constructive_explanation_abv': [unweakened_pro.get('branches_abv', []), added_con_abv],
                    'constructive_explanation_arg': [base_args, added_con_args]
                }
        
        # All con-branches added, try pro-weakening branches
        #breakpoint()  # DEBUG: Start adding pro-weakening branches
        pro_weak_ranking = pro_weakening.get('ranking', [])
        pro_weak_ranking_abv = pro_weakening.get('ranking_abv', [])
        
        added_pro_weak_args = []
        added_pro_weak_abv = []
        
        for i, pro_weak_args in enumerate(pro_weak_ranking):
            added_pro_weak_args.extend(pro_weak_args)
            if i < len(pro_weak_ranking_abv):  # Safety check
                added_pro_weak_abv.append(pro_weak_ranking_abv[i])
            
            current_args = base_args + added_con_args + added_pro_weak_args + [target_id]
            restriction = create_restriction(debate_data, current_args)
            final_weights = apply_qem_to_restriction(restriction)
            w1_target = final_weights.get(target_id, w0_target)
            
            if w1_target < w0_target:
                return {
                    'success': True,
                    'constructive_explanation_abv': [
                        unweakened_pro.get('branches_abv', []), 
                        added_con_abv,
                        added_pro_weak_abv
                    ],
                    'constructive_explanation_arg': [
                        base_args, 
                        added_con_args,
                        added_pro_weak_args
                    ]
                }
    
    # No explanation found
    #breakpoint()  # DEBUG: Algorithm failed to find explanation
    return {
        'success': False,
        'constructive_explanation_abv': [],
        'constructive_explanation_arg': []
    }

def save_constructive_explanations_csv(rankings_data: Dict, heuristic_explanations: Dict, output_path: str):
    """Save CSV with just essential columns and constructive explanations."""
    #breakpoint()  # DEBUG: Start saving CSV output
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header with essential columns only
            writer.writerow(['debate_id', 't_id', 'direction', 'heuristic', 
                           'constructive_explanation_abv', 'constructive_explanation_arg'])
            
            # Write one row per heuristic
            for heuristic in ['weak to strong', 'strong to weak', 'small to large']:
                if heuristic in heuristic_explanations:
                    explanation = heuristic_explanations[heuristic]
                    
                    writer.writerow([
                        rankings_data['debate_id'],
                        rankings_data['t_id'], 
                        rankings_data['direction'],
                        heuristic,
                        str(explanation['constructive_explanation_abv']),
                        str(explanation['constructive_explanation_arg'])
                    ])
        
        # Silent success - only print failures
        
    except Exception as e:
        print(f"Error saving explanations CSV {output_path}: {e}")

def process_constructive_explanations(rankings_folder: str, debates_folder: str, output_folder: str):
    """Process all ranking files and generate constructive explanations."""
    #breakpoint()  # DEBUG: Start of main processing function
    os.makedirs(output_folder, exist_ok=True)
    
    csv_files = [f for f in os.listdir(rankings_folder) if f.endswith('_rankings.csv')]
    print(f"Processing {len(csv_files)} ranking CSV files from '{rankings_folder}'")
    
    for csv_file in csv_files:
        #breakpoint()
        #breakpoint()  # DEBUG: Processing each CSV file
        # Load rankings data
        csv_path = os.path.join(rankings_folder, csv_file)
        rankings_data = load_branch_rankings_data(csv_path)
 

        if  not rankings_data['debate_id']:
            print(f"ERROR: {csv_file} - missing debate_id")
            continue
        if not rankings_data:
            print(f"ERROR: {csv_file} - No rankings data")
            continue
        
        
        # Find the correct debate filename by matching target_id
        debate_id = rankings_data['debate_id']
        target_id = rankings_data['t_id']
        debate_filename = None
        
        # Try to construct the expected filename based on the CSV filename pattern
        csv_filename = csv_file.replace('_rankings.csv', '.json')
        expected_filename = csv_filename.replace('_branches_', '_').split('_')[0:3]  # Get debate_id, TXofY, target_id parts
        if len(expected_filename) == 3:
            expected_json = f"{expected_filename[0]}_{expected_filename[1]}_{expected_filename[2]}.json"
            if os.path.exists(os.path.join(debates_folder, expected_json)):
                debate_filename = expected_json
        
        # Comment out all fallback matching logic to verify expected filename construction works
        # # If that doesn't work, try exact match
        # if not debate_filename:
        #     exact_filename = f"{debate_id}.json"
        #     if os.path.exists(os.path.join(debates_folder, exact_filename)):
        #         debate_filename = exact_filename
        
        # # If still not found, look for files with exact target_id match (not substring)
        # if not debate_filename:
        #     for filename in os.listdir(debates_folder):
        #         if (filename.startswith(f"{debate_id}_") and 
        #             filename.endswith(f"_{target_id}.json") and 
        #             filename.endswith('.json')):
        #             debate_filename = filename
        #             break
        
        # # If still not found, look for files that contain the target_id (substring match as fallback)
        # if not debate_filename:
        #     for filename in os.listdir(debates_folder):
        #         if filename.startswith(f"{debate_id}_") and target_id in filename and filename.endswith('.json'):
        #             debate_filename = filename
        #             break
        
        # # Last resort: any file starting with debate_id
        # if not debate_filename:
        #     for filename in os.listdir(debates_folder):
        #         if filename.startswith(f"{debate_id}_") and filename.endswith('.json'):
        #             debate_filename = filename
        #             break
        
        if not debate_filename:
            print(f"ERROR: {csv_file} - Could not find debate file for debate_id {debate_id}")
            print(f"Expected filename: {expected_json if 'expected_json' in locals() else 'N/A'}")
            print(f"CSV filename: {csv_file}")
            print(f"CSV filename parts: {csv_filename.replace('_branches_', '_').split('_')[0:3] if 'csv_filename' in locals() else 'N/A'}")
            print("STOPPING EXECUTION to verify filename matching logic")
            exit(1)
            
        debate_data = load_debate_data(debate_filename, debates_folder)
        
        if not debate_data:
            print(f"ERROR: {csv_file} - Could not load debate data for {debate_filename}")
            continue
        
        # Generate explanations for each heuristic (once per heuristic, not per category)
        heuristics = ['weak to strong', 'strong to weak', 'small to large']
        heuristic_explanations = {}
        
        for heuristic in heuristics:
            if heuristic in rankings_data['rankings']:
                explanation = generate_constructive_explanation(rankings_data, debate_data, heuristic)
                heuristic_explanations[heuristic] = explanation
                
                # Only print failures
                if not explanation['success']:
                    print(f"FAILED: {csv_file} - {heuristic}")
        
        # Save constructive explanations CSV for this debate+target
        output_filename = csv_file.replace('_rankings.csv', '_constructive_explanations.csv')
        output_path = os.path.join(output_folder, output_filename)
        save_constructive_explanations_csv(rankings_data, heuristic_explanations, output_path)

if __name__ == "__main__":
    rankings_folder = "debate_branches_ranking"
    debates_folder = "debates_with_target_weight_change"
    output_folder = "constructive_explanations"

    process_constructive_explanations(rankings_folder, debates_folder, output_folder)