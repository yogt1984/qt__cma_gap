"""
Module for visualizing CME gaps and statistics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from typing import Optional


def plot_gap_statistics(gaps_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """
    Create multiple plots showing gap statistics.
    
    Args:
        gaps_df: DataFrame with gap data
        save_path: Optional path to save the figure
    """
    if gaps_df.empty:
        print("No gaps to visualize")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('CME Gap Statistics', fontsize=16, fontweight='bold')
    
    # 1. Gap size distribution
    ax1 = axes[0, 0]
    gaps_df['gap_size'].hist(bins=30, ax=ax1, edgecolor='black', alpha=0.7)
    ax1.axvline(gaps_df['gap_size'].mean(), color='red', linestyle='--', 
                label=f"Mean: ${gaps_df['gap_size'].mean():,.2f}")
    ax1.axvline(gaps_df['gap_size'].median(), color='green', linestyle='--', 
                label=f"Median: ${gaps_df['gap_size'].median():,.2f}")
    ax1.set_xlabel('Gap Size (USD)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Gap Size Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Gap size over time
    ax2 = axes[0, 1]
    colors = ['green' if x == 'up' else 'red' for x in gaps_df['gap_direction']]
    ax2.scatter(gaps_df['gap_start'], gaps_df['gap_size'], c=colors, alpha=0.6, s=50)
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Gap Size (USD)')
    ax2.set_title('Gap Size Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Closure time distribution (for closed gaps)
    ax3 = axes[1, 0]
    closed_gaps = gaps_df[gaps_df['is_closed']]
    if not closed_gaps.empty:
        closed_gaps['days_to_close'].hist(bins=30, ax=ax3, edgecolor='black', alpha=0.7, color='blue')
        ax3.axvline(closed_gaps['days_to_close'].mean(), color='red', linestyle='--', 
                    label=f"Mean: {closed_gaps['days_to_close'].mean():.2f} days")
        ax3.axvline(closed_gaps['days_to_close'].median(), color='green', linestyle='--', 
                    label=f"Median: {closed_gaps['days_to_close'].median():.2f} days")
        ax3.set_xlabel('Days to Close')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Gap Closure Time Distribution')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No closed gaps', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Gap Closure Time Distribution')
    
    # 4. Closure rate by gap size
    ax4 = axes[1, 1]
    # Bin gaps by size
    gap_bins = pd.cut(gaps_df['gap_size'].abs(), bins=10)
    bin_stats = gaps_df.groupby(gap_bins).agg({
        'is_closed': ['sum', 'count']
    })
    bin_stats.columns = ['closed', 'total']
    bin_stats['closure_rate'] = (bin_stats['closed'] / bin_stats['total'] * 100)
    bin_centers = [interval.mid for interval in bin_stats.index]
    
    ax4.bar(range(len(bin_stats)), bin_stats['closure_rate'], alpha=0.7, color='steelblue')
    ax4.set_xlabel('Gap Size Bin')
    ax4.set_ylabel('Closure Rate (%)')
    ax4.set_title('Closure Rate by Gap Size')
    ax4.set_xticks(range(len(bin_stats)))
    ax4.set_xticklabels([f"${interval.left:.0f}-${interval.right:.0f}" 
                         for interval in bin_stats.index], rotation=45, ha='right')
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Statistics plot saved to {save_path}")
    else:
        plt.show()


def plot_price_action_with_gaps(
    df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    save_path: Optional[str] = None
) -> None:
    """
    Plot Bitcoin price action with CME gaps highlighted.
    
    Args:
        df: Price DataFrame
        gaps_df: DataFrame with gap data
        start_date: Optional start date for the plot
        end_date: Optional end date for the plot
        save_path: Optional path to save the figure
    """
    if df.empty:
        print("No price data to visualize")
        return
    
    # Filter data by date range if provided
    if start_date:
        df_plot = df[df['timestamp'] >= pd.Timestamp(start_date)].copy()
    else:
        df_plot = df.copy()
    
    if end_date:
        df_plot = df_plot[df_plot['timestamp'] <= pd.Timestamp(end_date)].copy()
    
    if df_plot.empty:
        print("No data in specified date range")
        return
    
    # Filter gaps in date range
    if start_date:
        gaps_plot = gaps_df[gaps_df['gap_start'] >= pd.Timestamp(start_date)].copy()
    else:
        gaps_plot = gaps_df.copy()
    
    if end_date:
        gaps_plot = gaps_plot[gaps_plot['gap_start'] <= pd.Timestamp(end_date)].copy()
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Plot price
    ax.plot(df_plot['timestamp'], df_plot['close'], label='BTC Price', linewidth=1.5, color='black', alpha=0.7)
    ax.fill_between(df_plot['timestamp'], df_plot['low'], df_plot['high'], 
                     alpha=0.2, color='gray', label='Price Range')
    
    # Highlight gaps
    for idx, gap in gaps_plot.iterrows():
        gap_start = gap['gap_start']
        gap_end = gap['gap_end']
        close_price = gap['close_price']
        open_price = gap['open_price']
        
        # Draw gap rectangle
        color = 'green' if gap['gap_direction'] == 'up' else 'red'
        alpha = 0.3 if gap['is_closed'] else 0.5
        
        # Vertical line at gap start
        ax.axvline(gap_start, color=color, linestyle='--', alpha=0.5, linewidth=1)
        
        # Rectangle showing gap
        rect_width = (gap_end - gap_start).total_seconds() / 86400  # days
        ax.add_patch(plt.Rectangle(
            (mdates.date2num(gap_start), min(close_price, open_price)),
            rect_width,
            abs(open_price - close_price),
            fill=True,
            color=color,
            alpha=alpha,
            edgecolor=color,
            linewidth=1.5
        ))
        
        # Mark closure if closed
        if gap['is_closed']:
            closure_time = gap['closure_time']
            ax.scatter(closure_time, close_price, color='blue', s=100, 
                      marker='x', zorder=5, label='Gap Closure' if idx == gaps_plot.index[0] else '')
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price (USD)', fontsize=12)
    ax.set_title('Bitcoin Price Action with CME Gaps', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Price action plot saved to {save_path}")
    else:
        plt.show()


def plot_closure_analysis(gaps_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """
    Create detailed plots analyzing gap closures.
    
    Args:
        gaps_df: DataFrame with gap data
        save_path: Optional path to save the figure
    """
    if gaps_df.empty:
        print("No gaps to analyze")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Gap Closure Analysis', fontsize=16, fontweight='bold')
    
    closed_gaps = gaps_df[gaps_df['is_closed']]
    open_gaps = gaps_df[~gaps_df['is_closed']]
    
    # 1. Closure rate over time
    ax1 = axes[0, 0]
    gaps_df['year'] = pd.to_datetime(gaps_df['gap_start']).dt.year
    yearly_stats = gaps_df.groupby('year').agg({
        'is_closed': ['sum', 'count']
    })
    yearly_stats.columns = ['closed', 'total']
    yearly_stats['closure_rate'] = (yearly_stats['closed'] / yearly_stats['total'] * 100)
    
    ax1.plot(yearly_stats.index, yearly_stats['closure_rate'], marker='o', linewidth=2, markersize=8)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Closure Rate (%)')
    ax1.set_title('Closure Rate Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 105])
    
    # 2. Gap size vs closure time
    ax2 = axes[0, 1]
    if not closed_gaps.empty:
        scatter = ax2.scatter(closed_gaps['gap_size'].abs(), closed_gaps['days_to_close'],
                             c=closed_gaps['gap_size'], cmap='RdYlGn', s=60, alpha=0.6, edgecolors='black')
        ax2.set_xlabel('Gap Size (USD, absolute)')
        ax2.set_ylabel('Days to Close')
        ax2.set_title('Gap Size vs Closure Time')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax2, label='Gap Size (USD)')
    else:
        ax2.text(0.5, 0.5, 'No closed gaps', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Gap Size vs Closure Time')
    
    # 3. Open vs Closed gaps comparison
    ax3 = axes[1, 0]
    if not open_gaps.empty and not closed_gaps.empty:
        ax3.hist([closed_gaps['gap_size'].abs(), open_gaps['gap_size'].abs()],
                bins=20, label=['Closed', 'Open'], alpha=0.7, edgecolor='black')
        ax3.set_xlabel('Gap Size (USD, absolute)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Gap Size: Closed vs Open')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    elif not closed_gaps.empty:
        ax3.hist(closed_gaps['gap_size'].abs(), bins=20, label='Closed', alpha=0.7, edgecolor='black')
        ax3.set_xlabel('Gap Size (USD, absolute)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Gap Size: Closed Gaps')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No closed gaps', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Gap Size: Closed vs Open')
    
    # 4. Cumulative closure rate
    ax4 = axes[1, 1]
    gaps_sorted = gaps_df.sort_values('gap_start').copy()
    gaps_sorted['cumulative_closed'] = gaps_sorted['is_closed'].cumsum()
    gaps_sorted['cumulative_total'] = range(1, len(gaps_sorted) + 1)
    gaps_sorted['cumulative_rate'] = (gaps_sorted['cumulative_closed'] / 
                                      gaps_sorted['cumulative_total'] * 100)
    
    ax4.plot(gaps_sorted['gap_start'], gaps_sorted['cumulative_rate'], linewidth=2)
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Cumulative Closure Rate (%)')
    ax4.set_title('Cumulative Closure Rate Over Time')
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax4.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Closure analysis plot saved to {save_path}")
    else:
        plt.show()

