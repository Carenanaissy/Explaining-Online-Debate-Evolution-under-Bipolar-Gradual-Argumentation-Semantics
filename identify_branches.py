import os
import json
import csv
from typing import List, Dict

def load_debate(file_path: str) -> Dict:
    """
    Load a JSON debate file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return {}

def is_significant(argument: Dict) -> bool:
    """
    Check if an argument is significant (final weight ≠ 0).
    """
    return argument.get('final_weight', 0.0) != 0.0

def identify_branches(debate: Dict, target: str):
    """
    Identify pro-branches, con-branches, unweakened branches, and weakening sub-branches.
    """
    nodes = debate.get('nodes', {})
    edges = debate.get('edges', {})

    # Separate significant supporters and attackers of the target
    significant_supporters = []
    significant_attackers = []

    for edge_id, edge_data in edges.items():
        if edge_data.get('successor_id') == target:
            source_node = nodes.get(edge_id)
            if source_node and is_significant(source_node):
                relation = edge_data.get('relation', 0)
                if relation > 0:  # Support relation
                    significant_supporters.append(edge_id)
                elif relation < 0:  # Attack relation
                    significant_attackers.append(edge_id)

    # Ensure roots of all branches are significant
    def is_significant_root(arg_id):
        return arg_id in nodes and is_significant(nodes[arg_id])

    # Helper function to traverse and collect full branches
    def traverse_full_branch(root_id):
        branch = []
        stack = [root_id]
        visited = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            branch.append(current)

            # Look for ALL edges where current is the successor (follow all paths backward)
            for edge_id, edge_data in edges.items():
                if edge_data.get('successor_id') == current:
                    relation = edge_data.get('relation', 0)
                    if relation != 0.0:  # Any non-zero relation
                        stack.append(edge_id)

        return branch

    # Identify pro-branches and con-branches
    pro_branches = [traverse_full_branch(root) for root in significant_supporters if is_significant_root(root)]
    con_branches = [traverse_full_branch(root) for root in significant_attackers if is_significant_root(root)]

    # Helper function to compute path sign from argument to target
    def compute_path_sign_significant_only(arg_id, target_id):
       
        if arg_id == target_id:
            return 1  # Target to itself is positive
        
        # Check if starting argument is significant
        if arg_id not in nodes or not is_significant(nodes[arg_id]):
            return 0  # Starting argument is not significant
        
        # BFS to find path from arg_id to target_id through significant arguments only
        from collections import deque
        queue = deque([(arg_id, 1)])  # (current_node, current_path_sign)
        visited = set()
        
        while queue:
            current, path_sign = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            if current == target_id:
                return path_sign
            
            # Look for outgoing edges from current node
            for edge_id, edge_data in edges.items():
                if edge_id == current:
                    successor = edge_data.get('successor_id')
                    relation = edge_data.get('relation', 0.0)
                    # Only continue if successor exists, relation is non-zero, and successor is significant
                    if (successor and relation != 0.0 and 
                        successor in nodes and is_significant(nodes[successor])):
                        new_path_sign = path_sign * (1 if relation > 0 else -1)
                        queue.append((successor, new_path_sign))
        return 0  # No path found through significant arguments
    
    # Helper function to check if argument is pro or con (through significant path only)
    def is_pro_argument(arg_id):
        return compute_path_sign_significant_only(arg_id, target) > 0
    
    def is_con_argument(arg_id):
        return compute_path_sign_significant_only(arg_id, target) < 0
    
    
    # Helper function to traverse unweakened branches
    def traverse_unweakened_branch(root_id, expected_type):
        branch = []
        stack = [root_id]
        visited = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            
            # Check if current argument matches expected type
            if expected_type == "pro" and is_pro_argument(current):
                branch.append(current)
                # Continue following paths only if argument is pro
                for edge_id, edge_data in edges.items():
                    if edge_data.get('successor_id') == current:
                        relation = edge_data.get('relation', 0)
                        if relation != 0.0:
                            stack.append(edge_id)
            elif expected_type == "con" and is_con_argument(current):
                branch.append(current)
                # Continue following paths only if argument is con
                for edge_id, edge_data in edges.items():
                    if edge_data.get('successor_id') == current:
                        relation = edge_data.get('relation', 0)
                        if relation != 0.0:
                            stack.append(edge_id)
            elif current == root_id:
                # Always include the root, even if it doesn't match expected type
                branch.append(current)
                # But don't continue traversal if root doesn't match

        return branch

    # Find unweakened branches
    def find_unweakened_branches(supporters_or_attackers, expected_type):
        unweakened_branches = []
        
        for root in supporters_or_attackers:
            if is_significant_root(root):
                branch = traverse_unweakened_branch(root, expected_type)
                
                # Only include if branch has more than just the root and all are expected type
                if len(branch) > 0:
                    all_expected_type = True
                    for arg_id in branch:
                        if expected_type == "pro" and not is_pro_argument(arg_id):
                            all_expected_type = False
                            break
                        elif expected_type == "con" and not is_con_argument(arg_id):
                            all_expected_type = False
                            break
                    
                    if all_expected_type:
                        unweakened_branches.append(branch)
        
        return unweakened_branches
    
    unweakened_pro_branches = find_unweakened_branches(significant_supporters, "pro")
    unweakened_con_branches = find_unweakened_branches(significant_attackers, "con")

    # Helper function to find all pro/con arguments in unweakened branches
    def get_arguments_from_unweakened_branches(unweakened_branches):
        arguments_set = set()
        for branch in unweakened_branches:
            for arg_id in branch:
                arguments_set.add(arg_id)
        return arguments_set

    # Get all pro-arguments and con-arguments from unweakened branches
    pro_arguments_in_unweakened = get_arguments_from_unweakened_branches(unweakened_pro_branches)
    con_arguments_in_unweakened = get_arguments_from_unweakened_branches(unweakened_con_branches)

    # Find pro-weakening sub-branches: sub-branches that attack pro-arguments in unweakened pro-branches
    def find_pro_weakening_sub_branches():
        pro_weakening_sub_branches = []
        
        for edge_id, edge_data in edges.items():
            successor_id = edge_data.get('successor_id')
            relation = edge_data.get('relation', 0)
            
            # Check if this edge attacks a pro-argument from an unweakened pro-branch
            if (relation < 0 and 
                successor_id in pro_arguments_in_unweakened and 
                is_significant_root(edge_id)):
                
                # This is a significant attacker of a pro-argument in an unweakened pro-branch
                sub_branch = traverse_full_branch(edge_id)
                pro_weakening_sub_branches.append(sub_branch)
                
        return pro_weakening_sub_branches

    # Find con-weakening sub-branches: sub-branches that attack con-arguments in unweakened con-branches  
    def find_con_weakening_sub_branches():
        con_weakening_sub_branches = []
        
        for edge_id, edge_data in edges.items():
            successor_id = edge_data.get('successor_id')
            relation = edge_data.get('relation', 0)
            
            # Check if this edge attacks a con-argument from an unweakened con-branch
            if (relation < 0 and 
                successor_id in con_arguments_in_unweakened and 
                is_significant_root(edge_id)):
                
                # This is a significant attacker of a con-argument in an unweakened con-branch
                sub_branch = traverse_full_branch(edge_id)
                con_weakening_sub_branches.append(sub_branch)
                
        return con_weakening_sub_branches

    pro_weakening_sub_branches = find_pro_weakening_sub_branches()
    con_weakening_sub_branches = find_con_weakening_sub_branches()

    # Output results (console)
    #print("Pro-Branches:", pro_branches)
    #print("Con-Branches:", con_branches)
    #print("Unweakened Pro-Branches:", unweakened_pro_branches)
    #print("Unweakened Con-Branches:", unweakened_con_branches)
    #print("Pro-Weakening Sub-Branches:", pro_weakening_sub_branches)
    #print("Con-Weakening Sub-Branches:", con_weakening_sub_branches)
    
    # Return results for CSV export
    return {
        'pro_branches': pro_branches,
        'con_branches': con_branches,
        'unweakened_pro_branches': unweakened_pro_branches,
        'unweakened_con_branches': unweakened_con_branches,
        'pro_weakening_sub_branches': pro_weakening_sub_branches,
        'con_weakening_sub_branches': con_weakening_sub_branches
    }

def save_branches_to_csv(file_name: str, target: str, branches_data: Dict, output_folder: str, total_nodes: int):
    """
    Save branch data to CSV file in the output folder.
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Create CSV filename with total nodes count
    base_name = file_name.replace('.json', '')
    csv_filename = f"{base_name}_branches_{total_nodes}nodes.csv"
    csv_path = os.path.join(output_folder, csv_filename)
    
    # Prepare data for CSV
    rows = []
    
    # Add pro-branches
    for i, branch in enumerate(branches_data['pro_branches'], 1):
        rows.append(['Pro-branch', f'Pb{i}', len(branch), ','.join(branch)])
    
    # Add con-branches
    for i, branch in enumerate(branches_data['con_branches'], 1):
        rows.append(['Con-branch', f'Cb{i}', len(branch), ','.join(branch)])
    
    # Add unweakened pro-branches
    for i, branch in enumerate(branches_data['unweakened_pro_branches'], 1):
        rows.append(['Unweakened Pro-branch', f'UnWPb{i}', len(branch), ','.join(branch)])
    
    # Add unweakened con-branches
    for i, branch in enumerate(branches_data['unweakened_con_branches'], 1):
        rows.append(['Unweakened Con-branch', f'UnWCb{i}', len(branch), ','.join(branch)])
    
    # Add pro-weakening sub-branches
    for i, branch in enumerate(branches_data['pro_weakening_sub_branches'], 1):
        rows.append(['Pro-Weakening branch', f'PWb{i}', len(branch), ','.join(branch)])
    
    # Add con-weakening sub-branches
    for i, branch in enumerate(branches_data['con_weakening_sub_branches'], 1):
        rows.append(['Con-Weakening branch', f'CWb{i}', len(branch), ','.join(branch)])
    
    # Write to CSV
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['Branch_Type', 'Branch_ID', 'Size', 'Arguments'])
            # Write metadata
            writer.writerow(['# Debate File:', file_name, '', ''])
            writer.writerow(['# Target Argument:', target, '', ''])
            writer.writerow(['# Total Branches:', len(rows), '', ''])
            writer.writerow([])  # Empty row for separation
            # Write branch data
            writer.writerows(rows)
        
        print(f"Saved branches to: {csv_path}")
    except Exception as e:
        print(f"Error saving CSV file {csv_path}: {e}")

def process_debates(folder_path: str):
    """
    Process all debates in the given folder and save results to CSV files.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist!")
        return
    
    output_folder = "debate_branches"
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    print(f"Found {len(json_files)} JSON files in '{folder_path}'")
    
    for file_name in json_files:
        file_path = os.path.join(folder_path, file_name)
        debate = load_debate(file_path)

        if debate:
            # Extract target from filename (e.g., "59355_T1of1_59355.3" -> "59355.3")
            target = file_name.split('_')[-1].replace('.json', '')
            #breakpoint()
            total_nodes = len(debate.get('nodes', {}))

            
            print(f"\nProcessing debate: {file_name}")
            #print(f"Target argument: {target}")
            #print(f"Number of nodes: {total_nodes}")
            #print(f"Number of edges: {len(debate.get('edges', {}))}")
            
            # Identify branches and get results
            branches_data = identify_branches(debate, target)
            
            # Save to CSV with node count in filename
            if branches_data:
                save_branches_to_csv(file_name, target, branches_data, output_folder, total_nodes)

if __name__ == "__main__":
    folder = "debates_with_target_weight_change"
    process_debates(folder)