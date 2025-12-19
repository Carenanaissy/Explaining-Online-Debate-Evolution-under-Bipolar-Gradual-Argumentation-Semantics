#!/usr/bin/env python3
"""
Compute coverage statistics by size category for each method and create bar plot
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

def load_and_process_data():
    """Load and process all CSV files from size_explanation directory"""
    print("📁 Loading data files...")
    
    # Find all CSV files
    files = glob.glob("size_explanation/*.csv")
    print(f"📊 Found {len(files)} files")
    
    all_data = []
    processed_count = 0
    
    for file_path in files:
        try:
            # Read CSV file
            df_file = pd.read_csv(file_path)
            source_filename = os.path.basename(file_path).replace('.csv', '')
            
            # Process each row
            for _, row in df_file.iterrows():
                try:
                    all_data.append({
                        'source_filename': source_filename,
                        'explanation_type': row['explanation_type'],
                        'heuristic': row['ranking'],
                        'target_arg': float(row['t_id']),
                        'num_args': int(row['total_graph_args']),
                        'needed_args': int(row['count_args_returned']),
                        'coverage_pct': float(row['pct_args_of_graph'])
                    })
                except (ValueError, KeyError) as e:
                    continue
            
            processed_count += 1
            if processed_count % 1000 == 0:
                print(f"   Processed {processed_count:,} files...")
                
        except Exception as e:
            continue
    
    print(f"✅ Successfully loaded {len(all_data):,} records from {processed_count:,} files")
    return pd.DataFrame(all_data)

def compute_category_breakpoints_from_data(df):
    """
    Compute the actual category breakpoints from the debate size data.
    This function shows exactly how we derived the values 23, 32, 50, 115.
    
    Returns: dictionary with computed breakpoints and explanation
    """
    print("\n🔢 COMPUTING SIZE CATEGORY BREAKPOINTS:")
    print("="*60)
    
    # Get unique debates (to avoid counting same debate multiple times)
    unique_debates = df.drop_duplicates(subset=['source_filename'])['num_args']
    
    # Compute key percentiles from actual data
    percentiles = {}
    for p in [50, 60, 70, 75, 80, 87.5, 90]:
        percentiles[p] = unique_debates.quantile(p/100)
        print(f"   {p:5.1f}th percentile: {percentiles[p]:6.1f} arguments")
    
    # Define our target breakpoints for balanced distribution
    print(f"\n📊 TARGET DISTRIBUTION:")
    print(f"   Very Small: 50.0% of debates (below median)")
    print(f"   Small:      12.5% of debates (50th to 62.5th percentile)")
    print(f"   Medium:     12.5% of debates (62.5th to 75th percentile)")
    print(f"   Large:      12.5% of debates (75th to 87.5th percentile)")
    print(f"   Very Large: 12.5% of debates (87.5th+ percentile)")
    
    # Compute breakpoints
    breakpoints = {}
    
    # Breakpoint 1: 50th percentile (median) - direct from data
    breakpoints['very_small_upper'] = percentiles[50]
    print(f"\n🎯 BREAKPOINT CALCULATIONS:")
    print(f"   Breakpoint 1 (Very Small | Small): {breakpoints['very_small_upper']:.1f}")
    print(f"      → 50th percentile (direct from data)")
    
    # Breakpoint 2: 62.5th percentile - interpolate between 60th and 70th
    # Linear interpolation: 62.5 is 25% of the way from 60 to 70
    # value = 60th + 0.25 * (70th - 60th)
    weight = (62.5 - 60) / (70 - 60)  # 0.25
    breakpoints['small_upper'] = percentiles[60] + weight * (percentiles[70] - percentiles[60])
    print(f"   Breakpoint 2 (Small | Medium): {breakpoints['small_upper']:.1f}")
    print(f"      → 62.5th percentile interpolated:")
    print(f"      → {percentiles[60]:.1f} + {weight:.3f} × ({percentiles[70]:.1f} - {percentiles[60]:.1f}) = {breakpoints['small_upper']:.1f}")
    
    # Breakpoint 3: 75th percentile - direct from data
    breakpoints['medium_upper'] = percentiles[75]
    print(f"   Breakpoint 3 (Medium | Large): {breakpoints['medium_upper']:.1f}")
    print(f"      → 75th percentile (direct from data)")
    
    # Breakpoint 4: 87.5th percentile - interpolate between 80th and 90th
    # Linear interpolation: 87.5 is 75% of the way from 80 to 90
    # value = 80th + 0.75 * (90th - 80th)
    weight = (87.5 - 80) / (90 - 80)  # 0.75
    breakpoints['large_upper'] = percentiles[80] + weight * (percentiles[90] - percentiles[80])
    print(f"   Breakpoint 4 (Large | Very Large): {breakpoints['large_upper']:.1f}")
    print(f"      → 87.5th percentile interpolated:")
    print(f"      → {percentiles[80]:.1f} + {weight:.3f} × ({percentiles[90]:.1f} - {percentiles[80]:.1f}) = {breakpoints['large_upper']:.1f}")
    
    # Round to reasonable integers for practical use
    rounded_breakpoints = {
        'very_small_upper': int(np.round(breakpoints['very_small_upper'])),
        'small_upper': int(np.round(breakpoints['small_upper'])), 
        'medium_upper': int(np.round(breakpoints['medium_upper'])),
        'large_upper': int(np.round(breakpoints['large_upper']))
    }
    
    print(f"\n✅ FINAL ROUNDED BREAKPOINTS:")
    print(f"   Very Small: < {rounded_breakpoints['very_small_upper']} arguments")
    print(f"   Small:      {rounded_breakpoints['very_small_upper']}-{rounded_breakpoints['small_upper']} arguments") 
    print(f"   Medium:     {rounded_breakpoints['small_upper']}-{rounded_breakpoints['medium_upper']} arguments")
    print(f"   Large:      {rounded_breakpoints['medium_upper']}-{rounded_breakpoints['large_upper']} arguments")
    print(f"   Very Large: {rounded_breakpoints['large_upper']}+ arguments")
    
    return {
        'exact_breakpoints': breakpoints,
        'rounded_breakpoints': rounded_breakpoints,
        'percentiles_used': percentiles
    }

def assign_size_categories(df):
    """Assign size categories based on empirical distribution analysis
    
    Categories derived from actual percentile analysis of 4,326 debates.
    See compute_category_breakpoints_from_data() for exact computation details.
    """
    
    # First, compute and display the actual breakpoints from data
    breakpoint_info = compute_category_breakpoints_from_data(df)
    rounded = breakpoint_info['rounded_breakpoints']
    
    # Use the computed breakpoints for categorization
    def get_category(num_args):
        if num_args < rounded['very_small_upper']:           # 50.0% - Very Small (below median)
            return 'Very Small'
        elif num_args < rounded['small_upper']:              # 12.5% - Small (50th to 62.5th percentile)
            return 'Small'
        elif num_args < rounded['medium_upper']:             # 12.5% - Medium (62.5th to 75th percentile)
            return 'Medium'
        elif num_args < rounded['large_upper']:              # 12.5% - Large (75th to 87.5th percentile)
            return 'Large'
        else:                                                # 12.5% - Very Large (87.5th+ percentile)
            return 'Very Large'
    
    df['size_category'] = df['num_args'].apply(get_category)
    return df

def create_method_by_size_bar_plot(df):
    """Create bar plot showing all methods across size categories"""
    
    # Create method labels
    df['method'] = df['explanation_type'] + ' + ' + df['heuristic'].str.replace('_', ' ').str.title()
    
    # Define orders
    method_order = [
        'constructive + Small To Large',
        'constructive + Strong To Weak', 
        'constructive + Weak To Strong',
        'destructive + Small To Large',
        'destructive + Strong To Weak',
        'destructive + Weak To Strong'
    ]
    
    size_order = ['Very Small', 'Small', 'Medium', 'Large', 'Very Large']
    
    # Calculate mean coverage by method and size
    stats = df.groupby(['method', 'size_category'])['coverage_pct'].agg(['mean', 'std', 'count']).reset_index()
    
    # Create pivot table for easier plotting
    pivot_mean = stats.pivot(index='method', columns='size_category', values='mean')
    pivot_std = stats.pivot(index='method', columns='size_category', values='std')
    
    # Reindex to ensure proper order
    pivot_mean = pivot_mean.reindex(method_order)[size_order]
    pivot_std = pivot_std.reindex(method_order)[size_order]
    
    # Create the plot with more space
    fig, ax = plt.subplots(figsize=(18, 12))
    
    # Set up bar positions
    x = np.arange(len(method_order))
    width = 0.14  # Slightly narrower bars for better spacing
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # One color per size category
    
    # Create bars for each size category
    for i, size_cat in enumerate(size_order):
        means = pivot_mean[size_cat].values
        stds = pivot_std[size_cat].values
        
        # Handle NaN values
        means = np.nan_to_num(means, 0)
        stds = np.nan_to_num(stds, 0)
        
        bars = ax.bar(x + i * width, means, width, 
                     yerr=stds, capsize=4,
                     label=size_cat, color=colors[i], 
                     alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Add value labels on bars with better positioning
        for j, (bar, mean_val) in enumerate(zip(bars, means)):
            if mean_val > 0:  # Only label non-zero bars
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + stds[j] + 2,
                       f'{mean_val:.1f}', ha='center', va='bottom', fontsize=7, rotation=90)
    
    # Customize the plot with better spacing
    ax.set_xlabel('Explanation-Heuristic Combination', fontsize=14, fontweight='bold', labelpad=15)
    ax.set_ylabel('Mean Argument Coverage (%)', fontsize=14, fontweight='bold')
    ax.set_title('Argument Coverage by Combination and Size Category\n(Mean ± Standard Deviation)', 
                fontsize=16, fontweight='bold', pad=15)
    
    # Set x-axis with better spacing
    ax.set_xticks(x + width * 2)  # Center the group labels
    ax.set_xticklabels([m.replace(' + ', '\n') for m in method_order], fontsize=10, ha='center')
    
    # Add legend positioned outside the plot area to avoid hiding data
    ax.legend(title='Size Category', fontsize=10, title_fontsize=11, 
              bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True, fancybox=True, shadow=True)
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Set y-axis limits with more space for labels
    ax.set_ylim(0, 110)
    
    # Improve layout with custom margins (more space on right for legend)
    plt.subplots_adjust(top=0.9, bottom=0.15, left=0.08, right=0.85)
    
    # Save the plot
    os.makedirs('debate_size_distribution_plots', exist_ok=True)
    output_path = 'debate_size_distribution_plots/methods_by_size_category_bar_plot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    print(f"💾 Saved bar plot: {output_path}")
    
    # Save detailed statistics to CSV
    csv_output_path = 'debate_size_distribution_plots/methods_by_size_category_statistics.csv'
    stats.to_csv(csv_output_path, index=False)
    print(f"💾 Saved statistics CSV: {csv_output_path}")
    
    plt.show()
    
    return stats

def compute_debate_size_distribution(df):
    """Compute and save debate size distribution"""
    print("📊 Computing debate size distribution...")
    
    # Get unique debates by source_filename (to avoid counting same debate multiple times)
    unique_debates = df.drop_duplicates(subset=['source_filename'])
    
    # Count debates by size category
    size_distribution = unique_debates['size_category'].value_counts().sort_index()
    
    # Calculate percentages
    total_debates = len(unique_debates)
    size_percentages = (size_distribution / total_debates * 100).round(2)
    
    # Create distribution DataFrame
    distribution_df = pd.DataFrame({
        'size_category': size_distribution.index,
        'count': size_distribution.values,
        'percentage': size_percentages.values
    })
    
    # Reorder according to logical size order
    size_order = ['Very Small', 'Small', 'Medium', 'Large', 'Very Large']
    distribution_df = distribution_df.set_index('size_category').reindex(size_order).reset_index()
    
    # Save to CSV
    os.makedirs('debate_size_distribution_plots', exist_ok=True)
    dist_csv_path = 'debate_size_distribution_plots/debate_size_distribution.csv'
    distribution_df.to_csv(dist_csv_path, index=False)
    print(f"💾 Saved size distribution: {dist_csv_path}")
    
    # Print distribution
    print("\n📈 DEBATE SIZE DISTRIBUTION:")
    print("="*50)
    for _, row in distribution_df.iterrows():
        category = row['size_category']
        count = int(row['count']) if not pd.isna(row['count']) else 0
        pct = row['percentage'] if not pd.isna(row['percentage']) else 0
        print(f"   {category:<12}: {count:>4,} debates ({pct:>5.1f}%)")
    
    print(f"   {'TOTAL':<12}: {total_debates:>4,} debates (100.0%)")
    
    return distribution_df

def save_detailed_statistics(df):
    """Save comprehensive statistics to CSV"""
    print("💾 Creating detailed statistics CSV...")
    
    # Create method labels
    df['method'] = df['explanation_type'] + ' + ' + df['heuristic'].str.replace('_', ' ').str.title()
    
    # Calculate comprehensive statistics
    detailed_stats = df.groupby(['method', 'size_category'])['coverage_pct'].agg([
        'count', 'mean', 'median', 'std', 'min', 'max',
        lambda x: x.quantile(0.25),  # Q1
        lambda x: x.quantile(0.75)   # Q3
    ]).round(2)
    
    # Rename the lambda columns
    detailed_stats.columns = ['count', 'mean', 'median', 'std', 'min', 'max', 'Q1', 'Q3']
    
    # Reset index to make it easier to work with
    detailed_stats = detailed_stats.reset_index()
    
    # Save to CSV
    os.makedirs('debate_size_distribution_plots', exist_ok=True)
    detailed_csv_path = 'debate_size_distribution_plots/detailed_statistics_by_method_and_size.csv'
    detailed_stats.to_csv(detailed_csv_path, index=False)
    print(f"💾 Saved detailed statistics: {detailed_csv_path}")
    
    return detailed_stats

def print_summary_statistics(stats, df):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("📊 SUMMARY STATISTICS BY METHOD AND SIZE CATEGORY")
    print("="*80)
    
    method_order = [
        'constructive + Small To Large',
        'constructive + Strong To Weak', 
        'constructive + Weak To Strong',
        'destructive + Small To Large',
        'destructive + Strong To Weak',
        'destructive + Weak To Strong'
    ]
    
    size_order = ['Very Small', 'Small', 'Medium', 'Large', 'Very Large']
    
    for method in method_order:
        print(f"\n🔍 {method.upper()}:")
        method_data = stats[stats['method'] == method]
        
        for size in size_order:
            size_data = method_data[method_data['size_category'] == size]
            if not size_data.empty:
                mean_val = size_data['mean'].iloc[0]
                std_val = size_data['std'].iloc[0] 
                count_val = size_data['count'].iloc[0]
                print(f"   {size:<12}: {mean_val:6.2f}% ± {std_val:5.2f}% (n={count_val:,})")
            else:
                print(f"   {size:<12}: No data")

def main():
    """Main execution function"""
    print("🚀 CREATING BAR PLOT BY SIZE CATEGORIES FOR ALL METHODS")
    print("="*70)
    
    # Load and process data
    df = load_and_process_data()
    
    if df.empty:
        print("❌ No data loaded. Please check your data files.")
        return
    
    # Assign size categories
    df = assign_size_categories(df)
    
    # Compute and save debate size distribution
    size_distribution = compute_debate_size_distribution(df)
    
    # Save detailed statistics
    detailed_stats = save_detailed_statistics(df)
    
    # Create visualization
    stats = create_method_by_size_bar_plot(df)
    
    # Print summary
    print_summary_statistics(stats, df)
    
    print("\n✅ ANALYSIS COMPLETED!")
    print("📁 Check 'debate_size_distribution_plots/methods_by_size_category_bar_plot.png'")

if __name__ == "__main__":
    main()