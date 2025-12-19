import os
import csv
import json
from typing import List, Dict, Tuple

def load_branch_data_from_csv(csv_path: str) -> Dict:
    """
    Load branch data from CSV file and organize by category.
    """
    #breakpoint()  # Breakpoint 1: Start of CSV loading
    branches = {
        'Pro-branch': [],
        'Con-branch': [],
        'Unweakened Pro-branch': [],
        'Unweakened Con-branch': [],
        'Pro-Weakening branch': [],
        'Con-Weakening branch': []
    }
    
    debate_file = ""
    target_arg = ""
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            for row in reader:
                if len(row) < 4:
                    continue
                
                # Extract metadata
                if row[0] == '# Debate File:':
                    debate_file = row[1]
                elif row[0] == '# Target Argument:':
                    target_arg = row[1]
                elif row[0] in branches:
                    # Parse branch data
                    #breakpoint()  # Breakpoint 2: Branch data parsing
                    branch_type = row[0]
                    branch_id = row[1]
                    size = int(row[2])
                    arguments = row[3].split(',') if row[3] else []
                    
                    branches[branch_type].append({
                        'id': branch_id,
                        'size': size,
                        'arguments': arguments
                    })
    
    except Exception as e:
        print(f"Error loading CSV {csv_path}: {e}")
        return {}
    
    return {
        'debate_file': debate_file,
        'target_argument': target_arg,
        'branches': branches
    }

def extract_debate_and_target_ids(filename: str) -> Tuple[str, str]:
    """
    Extract debate_id and t_id from filename like '7488_T1of1_7488.1_branches_55nodes.csv'
    """
    parts = filename.replace('.csv', '').split('_')
    debate_id = parts[0]
    t_id = parts[2]
    return debate_id, t_id

def load_debate_nodes(debate_file: str, debates_folder: str) -> Dict:
    """
    Load node data from the original debate JSON file.
    """
    debate_path = os.path.join(debates_folder, debate_file)
    
    try:
        with open(debate_path, 'r', encoding='utf-8') as file:
            debate_data = json.load(file)
            return debate_data.get('nodes', {})
    except Exception as e:
        print(f"Error loading debate file {debate_path}: {e}")
        return {}

def get_root_final_weight(branch: Dict, nodes: Dict) -> float:
    """
    Get the final weight of the branch's root argument.
    Assumes the first argument in the branch is the root.
    """
    if not branch['arguments']:
        return 0.0
    
    root_id = branch['arguments'][0]  # First argument is the root
    root_node = nodes.get(root_id, {})
    return root_node.get('final_weight', 0.0)

def determine_direction(target_id: str, nodes: Dict) -> str:
    """
    Determine if the target argument is strengthening or weakening.
    """
    #breakpoint()  # Breakpoint 3: Direction determination
    target_node = nodes.get(target_id, {})
    initial_weight = target_node.get('initial_weight', 0.0)
    final_weight = target_node.get('final_weight', 0.0)
    
    if final_weight > initial_weight:
        return "strengthening"
    elif final_weight < initial_weight:
        return "weakening"
    else:
        return "unchanged"

def apply_heuristics(branches: List[Dict], nodes: Dict) -> Dict:
    """
    Apply the three heuristics to rank branches:
    - weak to strong: Weakest to strongest (by root final weight)
    - strong to weak: Strongest to weakest (by root final weight)  
    - small to large: Smallest to largest (by number of arguments)
    """
    #breakpoint()  # Breakpoint 4: Heuristics application
    if not branches:
        return {
            'weak to strong': [],
            'strong to weak': [],
            'small to large': []
        }
    
    # Add final weights to branches for sorting
    branches_with_weights = []
    for branch in branches:
        branch_copy = branch.copy()
        branch_copy['root_weight'] = get_root_final_weight(branch, nodes)
        branches_with_weights.append(branch_copy)
    
    # Heuristic 1: weak to strong (Weakest to Strongest by root final weight)
    weak_to_strong = sorted(branches_with_weights, key=lambda x: x['root_weight'])
    
    # Heuristic 2: strong to weak (Strongest to Weakest by root final weight)
    strong_to_weak = sorted(branches_with_weights, key=lambda x: x['root_weight'], reverse=True)
    
    # Heuristic 3: small to large (Smallest to Largest by number of arguments)
    small_to_large = sorted(branches_with_weights, key=lambda x: x['size'])
    
    #breakpoint()  # Breakpoint 5: After heuristics sorting
    
    return {
        'weak to strong': weak_to_strong,
        'strong to weak': strong_to_weak,
        'small to large': small_to_large
    }

def save_rankings_to_csv(branch_data: Dict, nodes: Dict, debate_id: str, t_id: str, direction: str, output_path: str):
    """
    Save branch rankings to CSV file in the specified format.
    """
    #breakpoint()  # Breakpoint 6: Start of CSV saving
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            
            # Write header
            writer.writerow(['debate_id', 't_id', 'direction', 'heuristic', 'category', 'branches_abv', 'branches', 'ranking_abv', 'ranking'])
            
            # Map category names to standardized format
            category_mapping = {
                'Pro-branch': 'pro-branches',
                'Con-branch': 'con-branches',
                'Unweakened Pro-branch': 'unweakened pro-branches',
                'Unweakened Con-branch': 'unweakened con-branches',
                'Pro-Weakening branch': 'pro-weakening branches',
                'Con-Weakening branch': 'con-weakening branches'
            }
            
            # Process each branch category
            for category, branches in branch_data['branches'].items():
                if not branches:
                    continue
                
                #breakpoint()  # Breakpoint 7: Processing each category
                standardized_category = category_mapping.get(category, category.lower())
                
                # Apply heuristics
                rankings = apply_heuristics(branches, nodes)
                
                # Write rankings for each heuristic
                for heuristic, ranked_branches in rankings.items():
                    if not ranked_branches:
                        continue
                    
                    # Create branches_abv (original branch IDs before ranking)
                    branches_abv = [branch['id'] for branch in branches]
                    
                    # Create branches (original argument lists before ranking)
                    branches_list = [branch['arguments'] for branch in branches]
                    
                    # Create ranking_abv (list of branch IDs after ranking)
                    ranking_abv = [branch['id'] for branch in ranked_branches]
                    
                    # Create ranking (list of argument lists after ranking)
                    ranking = [branch['arguments'] for branch in ranked_branches]
                    
                    writer.writerow([
                        debate_id,
                        t_id,
                        direction,
                        heuristic,
                        standardized_category,
                        str(branches_abv),
                        str(branches_list),
                        str(ranking_abv),
                        str(ranking)
                    ])
        
        print(f"Saved rankings to: {output_path}")
        
    except Exception as e:
        print(f"Error saving rankings CSV {output_path}: {e}")

def process_branch_rankings(branches_folder: str, debates_folder: str, output_folder: str):
    """
    Process all CSV files in branches folder and generate rankings.
    """
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all CSV files from branches folder
    csv_files = [f for f in os.listdir(branches_folder) if f.endswith('.csv')]
    print(f"Found {len(csv_files)} CSV files in '{branches_folder}'")
    
    for csv_file in csv_files:
        print(f"\nProcessing: {csv_file}")
        #breakpoint()  # Breakpoint 8: Processing each file
        
        # Extract debate_id and t_id from filename
        debate_id, t_id = extract_debate_and_target_ids(csv_file)
        
        # Load branch data from CSV
        csv_path = os.path.join(branches_folder, csv_file)
        branch_data = load_branch_data_from_csv(csv_path)
        
        if not branch_data:
            continue
        
        # Load corresponding debate nodes
        nodes = load_debate_nodes(branch_data['debate_file'], debates_folder)
        
        if not nodes:
            print(f"Warning: Could not load nodes for {branch_data['debate_file']}")
            continue
        
        # Determine direction based on target argument
        direction = determine_direction(branch_data['target_argument'], nodes)
        
        #breakpoint()  # Breakpoint 9: Before saving rankings
        # Generate output filename
        output_filename = csv_file.replace('.csv', '_rankings.csv')
        output_path = os.path.join(output_folder, output_filename)
        
        # Save rankings
        save_rankings_to_csv(branch_data, nodes, debate_id, t_id, direction, output_path)

if __name__ == "__main__":
    branches_folder = "debate_branches"
    debates_folder = "debates_with_target_weight_change"
    output_folder = "debate_branches_ranking"
    
    process_branch_rankings(branches_folder, debates_folder, output_folder)