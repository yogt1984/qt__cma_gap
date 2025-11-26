"""
Module for calculating CME gap statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_gap_statistics(gaps_df: pd.DataFrame) -> Dict:
    """
    Calculate comprehensive statistics about CME gaps.
    
    Args:
        gaps_df: DataFrame with gap data (from detect_cme_gaps and find_gap_closures)
    
    Returns:
        Dictionary with statistics including:
        - total_gaps: Total number of gaps detected
        - closed_gaps: Number of closed gaps
        - open_gaps: Number of open gaps
        - closure_rate: Percentage of gaps that closed
        - avg_gap_size: Average gap size in USD
        - avg_gap_size_pct: Average gap size as percentage
        - median_gap_size: Median gap size in USD
        - largest_gap: Largest gap details
        - smallest_gap: Smallest gap details
        - avg_hours_to_close: Average hours to close (for closed gaps)
        - median_hours_to_close: Median hours to close
        - avg_days_to_close: Average days to close
        - up_gaps: Number of upward gaps
        - down_gaps: Number of downward gaps
        - up_gap_closure_rate: Closure rate for upward gaps
        - down_gap_closure_rate: Closure rate for downward gaps
        - gaps_closed_in_one_week: Number of gaps closed within 7 days
        - gaps_closed_in_one_week_pct: Percentage of all gaps closed within one week
        - gaps_closed_in_one_week_of_closed_pct: Percentage of closed gaps that closed within one week
    """
    if gaps_df.empty:
        return {
            'total_gaps': 0,
            'message': 'No gaps detected'
        }
    
    stats = {}
    
    # Basic counts
    stats['total_gaps'] = len(gaps_df)
    stats['closed_gaps'] = gaps_df['is_closed'].sum()
    stats['open_gaps'] = (~gaps_df['is_closed']).sum()
    stats['closure_rate'] = (stats['closed_gaps'] / stats['total_gaps'] * 100) if stats['total_gaps'] > 0 else 0
    
    # Gap size statistics
    stats['avg_gap_size'] = gaps_df['gap_size'].abs().mean()
    stats['avg_gap_size_pct'] = gaps_df['gap_size_pct'].abs().mean()
    stats['median_gap_size'] = gaps_df['gap_size'].abs().median()
    stats['std_gap_size'] = gaps_df['gap_size'].abs().std()
    
    # Largest and smallest gaps
    largest_idx = gaps_df['gap_size'].abs().idxmax()
    smallest_idx = gaps_df['gap_size'].abs().idxmin()
    
    stats['largest_gap'] = {
        'size': gaps_df.loc[largest_idx, 'gap_size'],
        'size_pct': gaps_df.loc[largest_idx, 'gap_size_pct'],
        'direction': gaps_df.loc[largest_idx, 'gap_direction'],
        'date': gaps_df.loc[largest_idx, 'gap_start'],
        'is_closed': gaps_df.loc[largest_idx, 'is_closed']
    }
    
    stats['smallest_gap'] = {
        'size': gaps_df.loc[smallest_idx, 'gap_size'],
        'size_pct': gaps_df.loc[smallest_idx, 'gap_size_pct'],
        'direction': gaps_df.loc[smallest_idx, 'gap_direction'],
        'date': gaps_df.loc[smallest_idx, 'gap_start'],
        'is_closed': gaps_df.loc[smallest_idx, 'is_closed']
    }
    
    # Closure time statistics (only for closed gaps)
    closed_gaps = gaps_df[gaps_df['is_closed']]
    if not closed_gaps.empty:
        stats['avg_hours_to_close'] = closed_gaps['hours_to_close'].mean()
        stats['median_hours_to_close'] = closed_gaps['hours_to_close'].median()
        stats['avg_days_to_close'] = closed_gaps['days_to_close'].mean()
        stats['median_days_to_close'] = closed_gaps['days_to_close'].median()
        stats['min_hours_to_close'] = closed_gaps['hours_to_close'].min()
        stats['max_hours_to_close'] = closed_gaps['hours_to_close'].max()
    else:
        stats['avg_hours_to_close'] = np.nan
        stats['median_hours_to_close'] = np.nan
        stats['avg_days_to_close'] = np.nan
        stats['median_days_to_close'] = np.nan
        stats['min_hours_to_close'] = np.nan
        stats['max_hours_to_close'] = np.nan
    
    # Direction statistics
    stats['up_gaps'] = (gaps_df['gap_direction'] == 'up').sum()
    stats['down_gaps'] = (gaps_df['gap_direction'] == 'down').sum()
    
    up_gaps = gaps_df[gaps_df['gap_direction'] == 'up']
    down_gaps = gaps_df[gaps_df['gap_direction'] == 'down']
    
    stats['up_gap_closure_rate'] = (up_gaps['is_closed'].sum() / len(up_gaps) * 100) if len(up_gaps) > 0 else 0
    stats['down_gap_closure_rate'] = (down_gaps['is_closed'].sum() / len(down_gaps) * 100) if len(down_gaps) > 0 else 0
    
    # Average gap sizes by direction
    stats['avg_up_gap_size'] = up_gaps['gap_size'].mean() if len(up_gaps) > 0 else 0
    stats['avg_down_gap_size'] = down_gaps['gap_size'].mean() if len(down_gaps) > 0 else 0
    
    # Gaps closed within one week (7 days)
    if not closed_gaps.empty:
        gaps_closed_in_week = closed_gaps[closed_gaps['days_to_close'] <= 7]
        stats['gaps_closed_in_one_week'] = len(gaps_closed_in_week)
        stats['gaps_closed_in_one_week_pct'] = (len(gaps_closed_in_week) / stats['total_gaps'] * 100) if stats['total_gaps'] > 0 else 0
        stats['gaps_closed_in_one_week_of_closed_pct'] = (len(gaps_closed_in_week) / stats['closed_gaps'] * 100) if stats['closed_gaps'] > 0 else 0
    else:
        stats['gaps_closed_in_one_week'] = 0
        stats['gaps_closed_in_one_week_pct'] = 0
        stats['gaps_closed_in_one_week_of_closed_pct'] = 0
    
    return stats


def print_statistics(stats: Dict) -> None:
    """Print statistics in a readable format."""
    print("\n" + "="*60)
    print("CME GAP STATISTICS")
    print("="*60)
    
    print(f"\nTotal Gaps Detected: {stats['total_gaps']}")
    print(f"  - Closed: {stats['closed_gaps']}")
    print(f"  - Open: {stats['open_gaps']}")
    print(f"  - Closure Rate: {stats['closure_rate']:.2f}%")
    
    print(f"\nGap Size Statistics:")
    print(f"  - Average: ${stats['avg_gap_size']:,.2f} ({stats['avg_gap_size_pct']:.2f}%)")
    print(f"  - Median: ${stats['median_gap_size']:,.2f}")
    print(f"  - Std Dev: ${stats['std_gap_size']:,.2f}")
    
    print(f"\nLargest Gap:")
    lg = stats['largest_gap']
    print(f"  - Size: ${lg['size']:,.2f} ({lg['size_pct']:.2f}%)")
    print(f"  - Direction: {lg['direction']}")
    print(f"  - Date: {lg['date']}")
    print(f"  - Closed: {lg['is_closed']}")
    
    print(f"\nSmallest Gap:")
    sg = stats['smallest_gap']
    print(f"  - Size: ${sg['size']:,.2f} ({sg['size_pct']:.2f}%)")
    print(f"  - Direction: {sg['direction']}")
    print(f"  - Date: {sg['date']}")
    print(f"  - Closed: {sg['is_closed']}")
    
    if not pd.isna(stats['avg_hours_to_close']):
        print(f"\nClosure Time Statistics (for closed gaps):")
        print(f"  - Average: {stats['avg_hours_to_close']:.1f} hours ({stats['avg_days_to_close']:.2f} days)")
        print(f"  - Median: {stats['median_hours_to_close']:.1f} hours ({stats['median_days_to_close']:.2f} days)")
        print(f"  - Range: {stats['min_hours_to_close']:.1f} - {stats['max_hours_to_close']:.1f} hours")
    
    print(f"\nDirection Statistics:")
    print(f"  - Upward Gaps: {stats['up_gaps']} (Closure Rate: {stats['up_gap_closure_rate']:.2f}%)")
    print(f"  - Downward Gaps: {stats['down_gaps']} (Closure Rate: {stats['down_gap_closure_rate']:.2f}%)")
    print(f"  - Avg Up Gap Size: ${stats['avg_up_gap_size']:,.2f}")
    print(f"  - Avg Down Gap Size: ${stats['avg_down_gap_size']:,.2f}")
    
    print(f"\nGaps Closed Within One Week:")
    print(f"  - Count: {stats['gaps_closed_in_one_week']} ({stats['gaps_closed_in_one_week_pct']:.2f}% of all gaps)")
    if stats['closed_gaps'] > 0:
        print(f"  - Percentage of closed gaps: {stats['gaps_closed_in_one_week_of_closed_pct']:.2f}%")
    
    print("="*60 + "\n")

