# Explaining Online Debate Evolution under Bipolar Gradual Argumentation Semantics
This repository contains the python scripts, data and results for generating and analyzing explanations of debate issues' weight changes induced by bipolar gradual argumentation semantics in Kialo debates. 

## Overview

The project analyzes debates where target arguments undergo weight changes after applying  bipolar gradual semantics. It identifies different types of branches and sub-branches in argumentation graphs, distinguishing between strengthening and weakening cases, and returns constructive and destructive explanations for a debate issue's weight change.


## Kialo Debates Dataset

The dataset consists of 2,959 anonymized debate JSON files extracted and cleaned from the Kialo debate platform. Each file represents a complete debate structure with arguments and their relations.


##  Scripts Description


1. **`compute_initial_weights_and_graphs.py`** - Computes initial argument weights using Yang et al. formula
2. **`compute_final_weights_and_graphs_QEM.py`** - Applies QEM semantics for final weight computation
3. **`extract_subdebates.py`** - Extracts individual sub-debates for each target argument
4. **`extract_debates_with_target_weight_change.py`** - Filters sub-debates to those with weight changes
5. **`analyze_weight_changes.py`** - Analyzes weight change patterns and provides statistics
6. **`identify_branches.py`** - Identifies  different types of argument branches
7. **`generate_branch_rankings.py`** - Generates rankings of branches using multiple heuristics
8. **`generate_constructive_explanations.py`** - Generates constructive explanations using the ranked branches
9. **`generate_destructive_explanations.py`** - Generates destructive explanations using the ranked branches
10. **`generate_size_analysis.py`** - Computes the  explanation size with respect to the number of arguments and to the number of branches for each explanation-heuristic combination
11. **`aggregate_explanation_stats.py`** - Aggregates the explanation size into final statistical summary with binning analysis
12. **`visualize_coverage_stats.py`** - Generates comprehensive visualizations from aggregated statistics
13. **`analyze_and_save_correlations.py`** - Analyzes correlations between weight changes and argument coverage by an explanation-heuristic combination
14. **`analyze_size_distribution.py`** - Analyzes the explanation size with respect to the debate 
15. **`create_methods_by_size_bar_plot.py`** - Creates comparative visualizations of explanation-heuristic combinations across debate size categories 
## Data Flow

```
Kialo_debates/ (2,959 anonymized JSON files)
         ↓
[compute_initial_weights_and_graphs.py]
         ↓
kialo_debates_initial_weights_added/ + graphs_initial_weights_added/
         ↓
[compute_final_weights_and_graphs_QEM.py]
         ↓
kialo_debates_final_weights_added/ + graphs_final_weights_added/
         ↓
[extract_subdebates.py]
         ↓
sub-debates/
         ↓
[extract_debates_with_target_weight_change.py]
         ↓
debates_with_target_weight_change/
         ↓
[analyze_weight_changes.py]
         ↓
Weight Change Statistics 
	 ↓
[identify_branches.py]
         ↓
debate_branches/ (Branch Analysis (CSV files))
         ↓
[generate_branch_rankings.py]
         ↓
debate_branches_ranking/ (Branch Rankings - Multiple Heuristics)
         ↓
[generate_constructive_explanations.py]
         ↓
constructive_explanations/
	 ↓
[generate_destructive_explanations.py]
         ↓
generated_constructive_destructive_explanations/
         ↓
[generate_size_analysis.py]
         ↓
size_explanation/ (4,326 size  files)
         ↓
[aggregate_explanation_stats.py]
         ↓
aggregated_explanation_stats.csv (Final Statistical Summary)
         ↓
[visualize_coverage_stats.py]
         ↓
coverage_plots/ (Visualization Charts)
         ↓
[analyze_and_save_correlations.py]
         ↓
correlation_analysis_output/ (Correlation Statistics & Plots)
         ↓
[analyze_size_distribution.py]
         ↓
debate_size_distribution_plots/ (Size Distribution Analysis & Statistics)
         ↓
[create_methods_by_size_bar_plot.py]
         ↓
Bar Plot Visualizations (Method Comparison by Size Category)
```



## File Formats

### Anonymized Debate JSON Structure

Each debate file follows this anonymized structure:

```json
{
  "nodes": {
    "debate_id.node_id": {
      "votes": {
        "0": 12,  // Count of votes with score 0
        "1": 8,   // Count of votes with score 1  
        "2": 15,  // Count of votes with score 2
        "3": 23,  // Count of votes with score 3
        "4": 7    // Count of votes with score 4
      }
    }
  },
  "edges": {
    "source_node_id": {
      "successor_id": "target_node_id",
      "relation": 1.0  // 1.0 = support, -1.0 = attack, 0.0 = no relation
    }
  }
}
```

### Vote Format

Votes are represented as aggregated counts by score level:
```json
"votes": {"4": 3}  // 3 votes with score 4
```



### Dataset Statistics

- **Total Debates**: 2,959 debate structures  
- **Sub-debates Extracted**: 5273 sub-debates extracted from the 2959 debates
- **Debates with Weight Changes**: 4,326 sub-debates showing  target weight changes
- **Strengthening Cases**: 2,529 debates (58.5%) where target arguments were strengthened
- **Weakening Cases**: 1,797 debates (41.5%) where target arguments were weakened
- **File Format**: JSON with consistent schema

## Explanation size with respect to the Number of Sub-trees

We also define the size of a returned explanation w.r.t. the number of sub-trees.  
- For **constructive explanations**: the number of returned pro-top-level sub-trees and con-weakening sub-trees for the strengthening case, and the number of returned con-top-level sub-trees and pro-weakening sub-trees for the weakening case.  
- For **destructive explanations**: the number of returned pro-top-level sub-trees for the strengthening case and returned con-top-level sub-trees for the weakening case.  

The percentage of sub-trees returned by an explanation is computed relative to the total number of sub-trees of the same categories in the corresponding case.  

| Strategy      | Heuristic           | Mean   | Median | Std Dev |
|---------------|-------------------|-------|--------|---------|
| Constructive  | H_{s → w}          | 54.24 | 50     | 30.1    |
| Constructive  | H_{w → s}          | 61.31 | 60     | 29.54   |
| Constructive  | H_{s → l}          | 59.6  | 57.14  | 30.2    |
| Destructive   | H_{s → w}          | 67.99 | 66.67  | 28.21   |
| Destructive   | H_{w → s}          | 78.11 | 87.5   | 25.6    |
| Destructive   | H_{s → l}          | 73.95 | 75     | 27.12   |

This table shows the mean, median, and standard deviation values computed for this percentage across the 4326 debates' explanations for each explanation-heuristic combination.

While generating constructive explanations following `H_{s → l}` gives the shortest explanations w.r.t. the number of arguments, using `H_{s → w}` gives the shortest explanations w.r.t. the number of branches, highlighting a trade-off between these two objectives.

We also observe higher standard deviation values for constructive explanations, leading to more variability in the percentage of returned branches. This may be explained by the variability in graph topology. For example, in the weakening case, every unweakened pro-top-level sub-tree **can** induce several pro-weakening sub-trees. The more a debate has unweakened pro-top-level sub-trees, the more likely it is to have pro-weakening sub-trees, which increases the total number of possible sub-trees. Unless a heuristic `H` returns all the pro-weakening sub-trees, a larger number of unweakened pro-top-level sub-trees will lower the percentage of returned sub-trees, whereas debates with only a few unweakened pro-top-level sub-trees can more easily reach high percentages.

## Requirements

- **Python 3.7+** for  scripts
- **JSON support** for data loading  
- **Standard libraries**: `json`, `os`, `csv` for basic operations

