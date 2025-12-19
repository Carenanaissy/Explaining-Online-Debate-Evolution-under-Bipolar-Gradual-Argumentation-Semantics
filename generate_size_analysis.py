#!/usr/bin/env python3


import os
import csv
import ast
import json
from typing import Dict, List, Tuple

def load_debate_data(debate_file: str, debates_folder: str) -> Dict:
    """
    Load debate JSON data to get total argument count.
    
    Args:
        debate_file: Name of the debate JSON file
        debates_folder: Path to the debates folder
    
    Returns:
        Dictionary containing debate data, or empty dict if error
    """
    debate_path = os.path.join(debates_folder, debate_file)
    
    # BREAKPOINT 1: Check file path construction
    #breakpoint()  # Debug: Verify debate_path is correct
    
    try:
        with open(debate_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        # BREAKPOINT 2: Inspect loaded debate data structure
        #breakpoint()  # Debug: Examine keys, argument count, structure
        return data
        
    except Exception as e:
        print(f"Error loading debate file {debate_path}: {e}")
        return {}

def load_branch_rankings_data(rankings_path: str) -> Dict:
    """
    Load branch rankings data to get total branch counts by category.
    
    This data is needed to calculate the denominator for branch coverage percentages.
    Different explanation types use different branch categories as their "universe":
    - Constructive: pro+con-weakening (strengthening) or con+pro-weakening (weakening)
    - Destructive: pro-only (strengthening) or con-only (weakening)
    
    Args:
        rankings_path: Path to the rankings CSV file
    
    Returns:
        Dictionary with rankings data organized by heuristic and category
    """
    data = {
        'debate_id': '',
        't_id': '',
        'direction': '',
        'rankings': {}
    }
    
    if not os.path.exists(rankings_path):
        print(f"ERROR: Rankings file not found: {rankings_path}")
        print("STOPPING EXECUTION to verify rankings file path")
        exit(1)
    
    try:
        with open(rankings_path, 'r', encoding='utf-8') as csvfile:
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
                    
                    # Initialize heuristic if not exists
                    if heuristic not in data['rankings']:
                        data['rankings'][heuristic] = {}
                    
                    # Parse branch data safely
                    try:
                        branches_abv_list = ast.literal_eval(branches_abv) if branches_abv else []
                        branches_list = ast.literal_eval(branches) if branches else []
                        
                        data['rankings'][heuristic][category] = {
                            'branches_abv': branches_abv_list,
                            'branches': branches_list,
                            'total_branches': len(branches_abv_list)  # Count of branches in this category
                        }
                        
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing branch data in {rankings_path}: {e}")
                        continue
    
    except Exception as e:
        print(f"Error loading rankings CSV {rankings_path}: {e}")
    
    return data

def count_arguments_in_explanation(explanation_arg: str) -> int:
    """
    Count total arguments in an explanation column.
    
    The explanation_arg column contains a list of lists, where each inner list
    represents arguments from different branch categories.
    
    Args:
        explanation_arg: String representation of nested list of arguments
    
    Returns:
        Total count of unique arguments in the explanation
    """
    try:
        # BREAKPOINT 3: Inspect raw explanation_arg string
        #breakpoint()  # Debug: Check format and content of explanation_arg
        
        # Parse the string representation of the nested list
        arg_lists = ast.literal_eval(explanation_arg) if explanation_arg else []
        
        # BREAKPOINT 4: Examine parsed argument lists structure
        #breakpoint()  # Debug: Verify parsing worked, check nested structure
        
        # Flatten all argument lists and count unique arguments
        all_args = set()  # Use set to avoid counting duplicates
        for arg_list in arg_lists:
            if isinstance(arg_list, list):
                all_args.update(arg_list)
        
        # BREAKPOINT 5: Check final argument count and unique args
        #breakpoint()  # Debug: Verify unique arguments and final count
        return len(all_args)
    
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing explanation arguments: {e}")
        return 0

def count_branches_in_explanation(explanation_abv: str, relevant_categories: List[str]) -> int:
    """
    Count branches in explanation for specific categories.
    
    The explanation_abv column contains a list where different positions
    correspond to different branch categories. We only count branches
    from categories that are relevant for the current explanation type.
    
    Args:
        explanation_abv: String representation of list of branch category lists
        relevant_categories: List of category indices to count (e.g., [1, 2] for positions 1 and 2)
    
    Returns:
        Total count of branches in relevant categories
    """
    try:
        # BREAKPOINT 6: Check branch explanation input and relevant categories
        #breakpoint()  # Debug: Inspect explanation_abv format and relevant_categories
        
        # Parse the string representation of the list
        branch_lists = ast.literal_eval(explanation_abv) if explanation_abv else []
        
        # BREAKPOINT 7: Examine parsed branch lists structure
        #breakpoint()  # Debug: Check branch_lists structure and length
        
        total_branches = 0
        
        # Count branches from relevant category positions
        for category_idx in relevant_categories:
            if category_idx < len(branch_lists):
                category_branches = branch_lists[category_idx]
                if isinstance(category_branches, list):
                    total_branches += len(category_branches)
        
        # BREAKPOINT 8: Verify final branch count
        #breakpoint()  # Debug: Check total_branches calculation
        return total_branches
    
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing explanation branches: {e}")
        return 0

def get_total_branches_for_explanation_type(rankings_data: Dict, heuristic: str, 
                                          explanation_type: str, direction: str) -> int:
    """
    Get total relevant branches for a specific explanation type and direction.
    
    Different explanation types use different sets of branches as their "universe":
    
    Constructive Explanations:
    - Strengthening: pro-branches + con-weakening branches
    - Weakening: con-branches + pro-weakening branches
    
    Destructive Explanations:
    - Strengthening: pro-branches only
    - Weakening: con-branches only
    
    Args:
        rankings_data: Branch rankings data
        heuristic: Heuristic name (e.g., 'weak to strong')
        explanation_type: 'constructive' or 'destructive'
        direction: 'strengthening' or 'weakening'
    
    Returns:
        Total count of relevant branches for this explanation type
    """
    heuristic_data = rankings_data['rankings'].get(heuristic, {})
    
    if explanation_type == 'constructive':
        if direction == 'strengthening':
            # Constructive strengthening uses pro-branches + con-weakening branches
            pro_count = heuristic_data.get('pro-branches', {}).get('total_branches', 0)
            con_weak_count = heuristic_data.get('con-weakening branches', {}).get('total_branches', 0)
            return pro_count + con_weak_count
        
        else:  # weakening
            # Constructive weakening uses con-branches + pro-weakening branches
            con_count = heuristic_data.get('con-branches', {}).get('total_branches', 0)
            pro_weak_count = heuristic_data.get('pro-weakening branches', {}).get('total_branches', 0)
            return con_count + pro_weak_count
    
    else:  # destructive
        if direction == 'strengthening':
            # Destructive strengthening uses pro-branches only
            return heuristic_data.get('pro-branches', {}).get('total_branches', 0)
        
        else:  # weakening
            # Destructive weakening uses con-branches only
            return heuristic_data.get('con-branches', {}).get('total_branches', 0)

def get_relevant_branch_categories(explanation_type: str, direction: str) -> List[int]:
    """
    Get the indices of relevant branch categories in explanation_abv.
    
    The explanation_abv column structure depends on the explanation type:
    
    Constructive explanations typically have structure:
    [base_branches, added_branches, additional_branches]
    
    Destructive explanations typically have structure:
    [unweakened_branches, weakening_branches, added_branches]
    
    Args:
        explanation_type: 'constructive' or 'destructive'
        direction: 'strengthening' or 'weakening'
    
    Returns:
        List of indices to count in the explanation_abv structure
    """
    if explanation_type == 'constructive':
        if direction == 'strengthening':
            # Constructive strengthening: count pro-branches and con-weakening branches
            # Typically positions [1] (pro-branches) and [2] (con-weakening)
            return [1, 2]
        else:  # weakening
            # Constructive weakening: count con-branches and pro-weakening branches
            # Typically positions [1] (con-branches) and [2] (pro-weakening)
            return [1, 2]
    
    else:  # destructive
        if direction == 'strengthening':
            # Destructive strengthening: count pro-branches only
            # Typically position [2] (added pro-branches)
            return [2]
        else:  # weakening
            # Destructive weakening: count con-branches only
            # Typically position [2] (added con-branches)
            return [2]

def process_combined_explanation_file(combined_file: str, combined_folder: str, 
                                    rankings_folder: str, debates_folder: str,
                                    output_folder: str):
    """
    Process a single combined explanation file and generate size analysis.
    
    For each debate+target combination, this creates 6 rows of analysis:
    - 3 rows for constructive explanations (one per heuristic)
    - 3 rows for destructive explanations (one per heuristic)
    
    Args:
        combined_file: Name of the combined explanation CSV file
        combined_folder: Path to combined explanations folder
        rankings_folder: Path to rankings folder
        debates_folder: Path to debates folder
        output_folder: Path to output folder for size analysis
    """
    print(f"Processing: {combined_file}")
    
    # BREAKPOINT 17: Check file processing inputs
    #breakpoint()  # Debug: Verify all folder paths and combined_file name
    
    # Load combined explanations data
    combined_path = os.path.join(combined_folder, combined_file)
    
    try:
        with open(combined_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            
            # BREAKPOINT 18: Inspect CSV header and structure
            #breakpoint()  # Debug: Check header format and column names
            
            # Read first row to get basic info
            first_row = next(reader)
            if len(first_row) < 8:
                print(f"ERROR: Insufficient columns in {combined_file}")
                print(f"Expected 8 columns, found {len(first_row)}")
                print(f"First row: {first_row}")
                print("STOPPING EXECUTION to verify combined file format")
                exit(1)
            
            debate_id, t_id, direction = first_row[0:3]
            
            # BREAKPOINT 19: Check extracted debate info
            #breakpoint()  # Debug: Verify debate_id, t_id, direction extraction
            
            # Reset file pointer to read all rows
            csvfile.seek(0)
            next(csv.reader(csvfile))  # Skip header again
            
    except Exception as e:
        print(f"ERROR reading combined file {combined_file}: {e}")
        print(f"Combined file path: {combined_path}")
        print("STOPPING EXECUTION to verify combined file format")
        exit(1)
    
    # Load corresponding rankings data
    rankings_file = combined_file.replace('_combined_explanations.csv', '_rankings.csv')
    rankings_path = os.path.join(rankings_folder, rankings_file)
    rankings_data = load_branch_rankings_data(rankings_path)
    
    if not rankings_data['debate_id']:
        print(f"ERROR: Could not load rankings data for {combined_file}")
        print(f"Expected rankings file: {rankings_file}")
        print(f"Rankings path: {rankings_path}")
        print("STOPPING EXECUTION to verify rankings file matching logic")
        exit(1)
    
    # Find corresponding debate file
    debate_filename = find_debate_file(debate_id, t_id, debates_folder)
    if not debate_filename:
        print(f"ERROR: Could not find debate file for {debate_id}")
        print(f"Target ID: {t_id}")
        print(f"Combined file: {combined_file}")
        print("STOPPING EXECUTION to verify debate file matching logic")
        exit(1)
    
    # Load debate data to get total argument count
    debate_data = load_debate_data(debate_filename, debates_folder)
    if not debate_data:
        print(f"ERROR: Could not load debate data for {debate_filename}")
        print(f"Debate file: {debate_filename}")
        print(f"Debates folder: {debates_folder}")
        print("STOPPING EXECUTION to verify debate data loading")
        exit(1)
    
    total_graph_args = len(debate_data.get('nodes', {}))
    
    # Prepare output data
    output_rows = []
    
    # Process each row in the combined file
    try:
        with open(combined_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 8:
                    debate_id, t_id, direction, heuristic = row[0:4]
                    constructive_abv, constructive_arg = row[4:6]
                    destructive_abv, destructive_arg = row[6:8]
                    
                    # Process constructive explanation
                    constructive_row = process_explanation_row(
                        debate_id, t_id, direction, heuristic,
                        'constructive', constructive_abv, constructive_arg,
                        total_graph_args, rankings_data
                    )
                    output_rows.append(constructive_row)
                    
                    # Process destructive explanation
                    destructive_row = process_explanation_row(
                        debate_id, t_id, direction, heuristic,
                        'destructive', destructive_abv, destructive_arg,
                        total_graph_args, rankings_data
                    )
                    output_rows.append(destructive_row)
    
    except Exception as e:
        print(f"ERROR processing rows in {combined_file}: {e}")
        print(f"Combined file: {combined_file}")
        print(f"Combined path: {combined_path}")
        print("STOPPING EXECUTION to verify row processing logic")
        exit(1)
    
    # Save output file
    output_filename = combined_file.replace('_combined_explanations.csv', '_size_analysis.csv')
    output_path = os.path.join(output_folder, output_filename)
    
    save_size_analysis_csv(output_rows, output_path)

def process_explanation_row(debate_id: str, t_id: str, direction: str, heuristic: str,
                          explanation_type: str, explanation_abv: str, explanation_arg: str,
                          total_graph_args: int, rankings_data: Dict) -> Dict:
    """
    Process a single explanation and calculate its size metrics.
    
    Args:
        debate_id: Debate identifier
        t_id: Target argument identifier
        direction: 'strengthening' or 'weakening'
        heuristic: Heuristic name
        explanation_type: 'constructive' or 'destructive'
        explanation_abv: Branch abbreviations in explanation
        explanation_arg: Arguments in explanation
        total_graph_args: Total arguments in the original graph
        rankings_data: Branch rankings data
    
    Returns:
        Dictionary with calculated size metrics
    """
    # BREAKPOINT 13: Check all input parameters
    #breakpoint()  # Debug: Verify all input values for this explanation row
    
    # Count arguments in explanation (+1 for target)
    count_args_returned = count_arguments_in_explanation(explanation_arg) + 1
    
    # Calculate argument coverage percentage
    pct_args_of_graph = (count_args_returned / total_graph_args * 100) if total_graph_args > 0 else 0
    
    # BREAKPOINT 14: Check argument counting and percentage
    #breakpoint()  # Debug: Verify count_args_returned and pct_args_of_graph

    # Get total relevant branches for this explanation type
    total_branches = get_total_branches_for_explanation_type(
        rankings_data, heuristic, explanation_type, direction
    )
    
    # Get relevant branch category indices
    relevant_categories = get_relevant_branch_categories(explanation_type, direction)
    
    # BREAKPOINT 15: Check branch totals and category mapping
    #breakpoint()  # Debug: Verify total_branches and relevant_categories

    # Count branches in explanation
    count_branches_returned = count_branches_in_explanation(explanation_abv, relevant_categories)
    
    # Calculate branch coverage percentage
    pct_branches_returned = (count_branches_returned / total_branches * 100) if total_branches > 0 else 0
    
    # BREAKPOINT 16: Final validation before return
    result = {
        'debate_id': debate_id,
        't_id': t_id,
        'direction': direction,
        'explanation_type': explanation_type,
        'ranking': heuristic.replace(' ', '_'),  # Convert to underscore format
        'total_graph_args': total_graph_args,
        'total_branches': total_branches,
        'count_args_returned': count_args_returned,
        'pct_args_of_graph': round(pct_args_of_graph, 2),
        'count_branches_returned': count_branches_returned,
        'pct_branches_returned': round(pct_branches_returned, 2)
    }
    #breakpoint()  # Debug: Inspect final result dictionary
    
    return result

def find_debate_file(debate_id: str, target_id: str, debates_folder: str) -> str:
    """
    Find the corresponding debate JSON file for a given debate_id and target_id.
    
    Uses multiple fallback strategies to locate the correct debate file.
    
    Args:
        debate_id: Debate identifier
        target_id: Target argument identifier  
        debates_folder: Path to debates folder
    
    Returns:
        Filename of the debate file, or None if not found
    """
    # Strategy 1: Try exact filename match
    exact_filename = f"{debate_id}_{target_id}.json"
    if os.path.exists(os.path.join(debates_folder, exact_filename)):
        return exact_filename
    
    # Strategy 2: Look for files with exact target_id match (not substring)
    # Pattern: {debate_id}_T{number}of{number}_{target_id}.json
    for filename in os.listdir(debates_folder):
        if (filename.startswith(f"{debate_id}_") and 
            filename.endswith(f"_{target_id}.json") and 
            filename.endswith('.json')):
            return filename
    
    # Comment out dangerous substring matching strategies
    # # Strategy 3: Look for files containing both debate_id and target_id (substring match)
    # for filename in os.listdir(debates_folder):
    #     if filename.startswith(f"{debate_id}_") and target_id in filename and filename.endswith('.json'):
    #         return filename
    
    # # Strategy 4: Any file starting with debate_id
    # for filename in os.listdir(debates_folder):
    #     if filename.startswith(f"{debate_id}_") and filename.endswith('.json'):
    #         return filename
    
    return None

def save_size_analysis_csv(output_rows: List[Dict], output_path: str):
    """
    Save size analysis results to CSV file.
    
    Args:
        output_rows: List of dictionaries containing size analysis data
        output_path: Path to output CSV file
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Define column order
            fieldnames = [
                'debate_id', 't_id', 'direction', 'explanation_type', 'ranking',
                'total_graph_args', 'total_branches', 'count_args_returned', 
                'pct_args_of_graph', 'count_branches_returned', 'pct_branches_returned'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write all rows
            for row in output_rows:
                writer.writerow(row)
                
        print(f"✓ Saved: {output_path}")
        
    except Exception as e:
        print(f"Error saving {output_path}: {e}")

def process_all_size_analyses():
    """
    Main function to process all combined explanation files and generate size analyses.
    
    This function:
    1. Creates the output directory
    2. Finds all combined explanation files
    3. Processes each file to generate size analysis
    4. Saves results in the size_explanation folder
    """
    # BREAKPOINT 20: Start of main processing function
    #breakpoint()  # Debug: Check current working directory and folder structure
    
    # Define folder paths
    combined_folder = "generated_constructive_destructive_explanations"
    rankings_folder = "debate_branches_ranking"
    debates_folder = "debates_with_target_weight_change"
    output_folder = "size_explanation"
    
    # Create output directory
    os.makedirs(output_folder, exist_ok=True)
    
    # Check if input folders exist
    for folder, name in [(combined_folder, "Combined explanations"), 
                        (rankings_folder, "Rankings"), 
                        (debates_folder, "Debates")]:
        if not os.path.exists(folder):
            print(f"ERROR: {name} folder '{folder}' not found")
            print(f"Current working directory: {os.getcwd()}")
            print("STOPPING EXECUTION to verify folder paths")
            exit(1)
    
    # Find all combined explanation files
    combined_files = [f for f in os.listdir(combined_folder) 
                     if f.endswith('_combined_explanations.csv')]
    
    if not combined_files:
        print(f"ERROR: No combined explanation files found in '{combined_folder}'")
        print(f"Folder contents: {os.listdir(combined_folder) if os.path.exists(combined_folder) else 'Folder does not exist'}")
        print("STOPPING EXECUTION to verify file discovery")
        exit(1)
    
    # BREAKPOINT 21: Check discovered files
    #breakpoint()  # Debug: Inspect combined_files list and count
    
    print(f"Found {len(combined_files)} combined explanation files to process")
    print(f"Output will be saved to: {output_folder}")
    print("-" * 60)
    
    # Process each file
    processed_count = 0
    error_count = 0
    
    # BREAKPOINT 22: Before processing loop starts
    #breakpoint()  # Debug: Ready to begin processing loop
    
    for combined_file in combined_files:
        try:
            # BREAKPOINT 23: Before processing each file (first few files only)
            #if processed_count < 3:  # Only break for first few files to avoid too many stops
                #breakpoint()  # Debug: About to process this specific file
                
            process_combined_explanation_file(
                combined_file, combined_folder, rankings_folder, 
                debates_folder, output_folder
            )
            processed_count += 1
            
            # Progress update every 100 files
            if processed_count % 100 == 0:
                print(f"Progress: {processed_count}/{len(combined_files)} files processed")
                
        except Exception as e:
            print(f"Error processing {combined_file}: {e}")
            error_count += 1
    
    # BREAKPOINT 24: Final completion summary
    #breakpoint()  # Debug: Check final counts and processing results
    
    # Final summary
    print("-" * 60)
    print(f"Processing complete!")
    print(f"Successfully processed: {processed_count} files")
    print(f"Errors encountered: {error_count} files")
    print(f"Output saved to: {output_folder}")
    
    if processed_count > 0:
        print(f"\nEach output file contains size analysis with:")
        print(f"- Argument coverage percentages")
        print(f"- Branch coverage percentages") 
        print(f"- 6 rows per debate (3 constructive + 3 destructive heuristics)")

if __name__ == "__main__":
    print("=" * 70)
    print("EXPLANATION SIZE ANALYSIS GENERATOR")
    print("=" * 70)
    print("This script analyzes the size of constructive and destructive explanations")
    print("by calculating argument and branch coverage percentages.")
    print()
    
    process_all_size_analyses()