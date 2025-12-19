#!/usr/bin/env python3
"""
Study debate size distribution to determine appropriate size categories
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

def analyze_debate_size_distribution():
    """Analyze the distribution of debate sizes to determine appropriate categories"""
    print("🔍 ANALYZING DEBATE SIZE DISTRIBUTION")
    print("="*50)
    
    # Ensure plots directory exists
    os.makedirs('debate_size_distribution_plots', exist_ok=True)
    
    # Load the data
    files = glob.glob("size_explanation/*.csv")
    print(f"📊 Found {len(files)} files")
    
    all_data = []
    processed_count = 0
    
    for file_path in files:
        try:
            df_file = pd.read_csv(file_path)
            source_filename = os.path.basename(file_path).replace('.csv', '')
            
            # Get unique debate size (take first row since all rows have same total_graph_args)
            if not df_file.empty:
                num_args = int(df_file['total_graph_args'].iloc[0])
                all_data.append({
                    'source_filename': source_filename,
                    'num_args': num_args
                })
            
            processed_count += 1
            if processed_count % 1000 == 0:
                print(f"   Processed {processed_count:,} files...")
                
        except Exception:
            continue
    
    df = pd.DataFrame(all_data)
    print(f"✅ Loaded {len(df):,} unique debates")
    
    # Basic statistics
    stats = {
        'min': df['num_args'].min(),
        'max': df['num_args'].max(),
        'mean': df['num_args'].mean(),
        'median': df['num_args'].median(),
        'std': df['num_args'].std(),
        'q25': df['num_args'].quantile(0.25),
        'q75': df['num_args'].quantile(0.75)
    }
    
    print(f"\n📈 BASIC STATISTICS:")
    print(f"   Min arguments:     {stats['min']:,}")
    print(f"   Max arguments:     {stats['max']:,}")
    print(f"   Mean arguments:    {stats['mean']:.1f}")
    print(f"   Median arguments:  {stats['median']:.1f}")
    print(f"   Std dev:           {stats['std']:.1f}")
    
    # Save statistics to CSV
    stats_df = pd.DataFrame([stats])
    stats_df.to_csv('debate_size_distribution_plots/debate_size_statistics.csv', index=False)
    print(f"💾 Saved debate size statistics: debate_size_distribution_plots/debate_size_statistics.csv")
    
    # Percentiles
    percentiles = [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]
    print(f"\n📊 PERCENTILES:")
    for p in percentiles:
        value = df['num_args'].quantile(p/100)
        print(f"   {p:2d}th percentile: {value:6.1f} arguments")
    
    # Create histogram
    plt.figure(figsize=(15, 10))
    
    # Main histogram
    plt.subplot(2, 2, 1)
    plt.hist(df['num_args'], bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Number of Arguments')
    plt.ylabel('Number of Debates')
    plt.title('Distribution of Debate Sizes (Full Range)')
    plt.grid(True, alpha=0.3)
    
    # Log scale histogram
    plt.subplot(2, 2, 2)
    plt.hist(df['num_args'], bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Number of Arguments')
    plt.ylabel('Number of Debates (Log Scale)')
    plt.title('Distribution of Debate Sizes (Log Scale)')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    
    # Box plot
    plt.subplot(2, 2, 3)
    plt.boxplot(df['num_args'], vert=True)
    plt.ylabel('Number of Arguments')
    plt.title('Box Plot of Debate Sizes')
    plt.grid(True, alpha=0.3)
    
    # Cumulative distribution
    plt.subplot(2, 2, 4)
    sorted_args = np.sort(df['num_args'])
    cumulative = np.arange(1, len(sorted_args) + 1) / len(sorted_args) * 100
    plt.plot(sorted_args, cumulative, linewidth=2)
    plt.xlabel('Number of Arguments')
    plt.ylabel('Cumulative Percentage')
    plt.title('Cumulative Distribution of Debate Sizes')
    plt.grid(True, alpha=0.3)
    
    # Add percentile lines
    for p in [25, 50, 75]:
        value = df['num_args'].quantile(p/100)
        plt.axvline(value, color='red', linestyle='--', alpha=0.7, label=f'{p}th percentile')
    plt.legend()
    
    plt.tight_layout()
    
    # Save the plot
    os.makedirs('debate_size_distribution_plots', exist_ok=True)
    plt.savefig('debate_size_distribution_plots/debate_size_distribution_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\n💾 Saved distribution analysis: debate_size_distribution_plots/debate_size_distribution_analysis.png")
    
    plt.show()
    

    
    # Save detailed data
    df.to_csv('debate_size_distribution_plots/debate_sizes_detailed.csv', index=False)
    print(f"\n💾 Saved detailed size data: debate_size_distribution_plots/debate_sizes_detailed.csv")

    return df

if __name__ == "__main__":
    analyze_debate_size_distribution()