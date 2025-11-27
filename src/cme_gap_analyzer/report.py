"""
Report generator for unclosed CME gaps.
Creates detailed analysis and visualizations of gaps that remain open.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cme_gap_analyzer.data_downloader import download_btc_candles
from cme_gap_analyzer.gap_detector import detect_cme_gaps, find_gap_closures
from cme_gap_analyzer.statistics import calculate_gap_statistics


def calculate_unclosed_gap_statistics(gaps_df: pd.DataFrame, df: pd.DataFrame) -> dict:
    """
    Calculate detailed statistics for unclosed gaps.
    
    Args:
        gaps_df: DataFrame with gap data
        df: Price DataFrame to get current price
    
    Returns:
        Dictionary with unclosed gap statistics
    """
    unclosed_gaps = gaps_df[~gaps_df['is_closed']].copy()
    
    if unclosed_gaps.empty:
        return {
            'total_unclosed': 0,
            'message': 'No unclosed gaps'
        }
    
    # Get current price (last price in the dataset)
    current_price = df['close'].iloc[-1]
    last_timestamp = df['timestamp'].iloc[-1]
    
    stats = {}
    stats['total_unclosed'] = len(unclosed_gaps)
    stats['current_price'] = current_price
    stats['last_timestamp'] = last_timestamp
    
    # Calculate days since gap creation
    unclosed_gaps = unclosed_gaps.copy()
    unclosed_gaps['days_since_gap'] = (last_timestamp - unclosed_gaps['gap_end']).dt.total_seconds() / 86400
    
    # Gap size statistics for unclosed gaps
    stats['avg_unclosed_gap_size'] = unclosed_gaps['gap_size'].abs().mean()
    stats['median_unclosed_gap_size'] = unclosed_gaps['gap_size'].abs().median()
    stats['max_unclosed_gap_size'] = unclosed_gaps['gap_size'].abs().max()
    stats['min_unclosed_gap_size'] = unclosed_gaps['gap_size'].abs().min()
    
    stats['avg_unclosed_gap_size_pct'] = unclosed_gaps['gap_size_pct'].abs().mean()
    
    # Direction breakdown
    stats['unclosed_up_gaps'] = (unclosed_gaps['gap_direction'] == 'up').sum()
    stats['unclosed_down_gaps'] = (unclosed_gaps['gap_direction'] == 'down').sum()
    
    # Time statistics
    stats['avg_days_since_gap'] = unclosed_gaps['days_since_gap'].mean()
    stats['median_days_since_gap'] = unclosed_gaps['days_since_gap'].median()
    stats['oldest_unclosed_gap_days'] = unclosed_gaps['days_since_gap'].max()
    stats['newest_unclosed_gap_days'] = unclosed_gaps['days_since_gap'].min()
    
    # Calculate distance to closure for each gap
    unclosed_gaps['distance_to_close'] = np.nan
    unclosed_gaps['distance_to_close_pct'] = np.nan
    
    for idx, gap in unclosed_gaps.iterrows():
        close_price = gap['close_price']
        if gap['gap_direction'] == 'up':
            # Upward gap: price needs to drop to close_price
            distance = current_price - close_price
            distance_pct = (distance / close_price) * 100
        else:
            # Downward gap: price needs to rise to close_price
            distance = close_price - current_price
            distance_pct = (distance / close_price) * 100
        
        unclosed_gaps.at[idx, 'distance_to_close'] = distance
        unclosed_gaps.at[idx, 'distance_to_close_pct'] = distance_pct
    
    stats['avg_distance_to_close'] = unclosed_gaps['distance_to_close'].abs().mean()
    stats['median_distance_to_close'] = unclosed_gaps['distance_to_close'].abs().median()
    stats['min_distance_to_close'] = unclosed_gaps['distance_to_close'].abs().min()
    stats['max_distance_to_close'] = unclosed_gaps['distance_to_close'].abs().max()
    
    stats['avg_distance_to_close_pct'] = unclosed_gaps['distance_to_close_pct'].abs().mean()
    
    # Store the detailed unclosed gaps dataframe
    stats['unclosed_gaps_df'] = unclosed_gaps
    
    return stats


def print_unclosed_gap_report(stats: dict) -> None:
    """Print a detailed report of unclosed gaps."""
    if stats.get('total_unclosed', 0) == 0:
        print("\n" + "="*70)
        print("UNCLOSED CME GAPS REPORT")
        print("="*70)
        print("\n✓ All CME gaps have been closed!")
        print("="*70 + "\n")
        return
    
    unclosed_gaps = stats['unclosed_gaps_df']
    
    print("\n" + "="*70)
    print("UNCLOSED CME GAPS REPORT")
    print("="*70)
    
    print(f"\n📊 SUMMARY")
    print(f"  Total Unclosed Gaps: {stats['total_unclosed']}")
    print(f"  Current BTC Price: ${stats['current_price']:,.2f}")
    print(f"  Report Date: {stats['last_timestamp']}")
    
    print(f"\n💰 GAP SIZE STATISTICS (Unclosed Gaps)")
    print(f"  Average Gap Size: ${stats['avg_unclosed_gap_size']:,.2f} ({stats['avg_unclosed_gap_size_pct']:.2f}%)")
    print(f"  Median Gap Size: ${stats['median_unclosed_gap_size']:,.2f}")
    print(f"  Largest Unclosed Gap: ${stats['max_unclosed_gap_size']:,.2f}")
    print(f"  Smallest Unclosed Gap: ${stats['min_unclosed_gap_size']:,.2f}")
    
    print(f"\n📈 DIRECTION BREAKDOWN")
    print(f"  Upward Gaps (Unclosed): {stats['unclosed_up_gaps']}")
    print(f"  Downward Gaps (Unclosed): {stats['unclosed_down_gaps']}")
    
    print(f"\n⏰ TIME STATISTICS")
    print(f"  Average Days Since Gap: {stats['avg_days_since_gap']:.1f} days")
    print(f"  Median Days Since Gap: {stats['median_days_since_gap']:.1f} days")
    print(f"  Oldest Unclosed Gap: {stats['oldest_unclosed_gap_days']:.1f} days ago")
    print(f"  Newest Unclosed Gap: {stats['newest_unclosed_gap_days']:.1f} days ago")
    
    print(f"\n🎯 DISTANCE TO CLOSURE")
    print(f"  Average Distance to Close: ${stats['avg_distance_to_close']:,.2f} ({stats['avg_distance_to_close_pct']:.2f}%)")
    print(f"  Median Distance to Close: ${stats['median_distance_to_close']:,.2f}")
    print(f"  Closest to Closure: ${stats['min_distance_to_close']:,.2f}")
    print(f"  Farthest from Closure: ${stats['max_distance_to_close']:,.2f}")
    
    print(f"\n📋 DETAILED LIST OF UNCLOSED GAPS")
    print("-"*70)
    print(f"{'#':<4} {'Date':<12} {'Direction':<10} {'Gap Size':<12} {'Gap %':<8} {'Days Ago':<10} {'Distance':<12} {'Distance %':<10}")
    print("-"*70)
    
    # Sort by gap size (largest first)
    unclosed_sorted = unclosed_gaps.sort_values('gap_size', key=abs, ascending=False)
    
    for idx, (row_idx, gap) in enumerate(unclosed_sorted.iterrows(), 1):
        gap_date = pd.Timestamp(gap['gap_start']).strftime('%Y-%m-%d')
        direction = gap['gap_direction'].upper()
        gap_size = gap['gap_size']
        gap_pct = gap['gap_size_pct']
        days_ago = gap['days_since_gap']
        distance = gap['distance_to_close']
        distance_pct = gap['distance_to_close_pct']
        
        print(f"{idx:<4} {gap_date:<12} {direction:<10} ${gap_size:>10,.2f} {gap_pct:>7.2f}% {days_ago:>9.1f} ${distance:>10,.2f} {distance_pct:>9.2f}%")
    
    print("="*70 + "\n")


def plot_unclosed_gaps_detailed(
    df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    stats: dict,
    save_path: str = None
) -> None:
    """Create detailed visualizations of unclosed gaps."""
    if stats.get('total_unclosed', 0) == 0:
        print("No unclosed gaps to visualize.")
        return
    
    unclosed_gaps = stats['unclosed_gaps_df']
    
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. Price chart with unclosed gaps highlighted
    ax1 = fig.add_subplot(gs[0, :])
    
    # Plot price
    ax1.plot(df['timestamp'], df['close'], label='BTC Price', linewidth=1.5, color='black', alpha=0.7)
    ax1.fill_between(df['timestamp'], df['low'], df['high'], alpha=0.2, color='gray', label='Price Range')
    
    # Highlight unclosed gaps
    for idx, gap in unclosed_gaps.iterrows():
        gap_start = gap['gap_start']
        gap_end = gap['gap_end']
        close_price = gap['close_price']
        open_price = gap['open_price']
        
        color = 'red' if gap['gap_direction'] == 'up' else 'green'
        
        # Draw vertical line at gap start
        ax1.axvline(gap_start, color=color, linestyle='--', alpha=0.6, linewidth=1.5)
        
        # Mark the gap closing price
        ax1.axhline(close_price, color=color, linestyle=':', alpha=0.5, linewidth=1)
        
        # Annotate with gap info
        ax1.annotate(
            f"${close_price:,.0f}\n{gap['gap_size_pct']:.2f}%",
            xy=(gap_start, close_price),
            xytext=(10, 10 if gap['gap_direction'] == 'up' else -30),
            textcoords='offset points',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color=color, alpha=0.6)
        )
    
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.set_title('Bitcoin Price with Unclosed CME Gaps Highlighted', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Gap size distribution
    ax2 = fig.add_subplot(gs[1, 0])
    unclosed_gaps['gap_size'].abs().hist(bins=15, ax=ax2, edgecolor='black', alpha=0.7, color='coral')
    ax2.axvline(unclosed_gaps['gap_size'].abs().mean(), color='red', linestyle='--', 
                label=f"Mean: ${unclosed_gaps['gap_size'].abs().mean():,.2f}")
    ax2.set_xlabel('Gap Size (USD, absolute)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Unclosed Gap Size Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Days since gap creation
    ax3 = fig.add_subplot(gs[1, 1])
    unclosed_gaps['days_since_gap'].hist(bins=15, ax=ax3, edgecolor='black', alpha=0.7, color='steelblue')
    ax3.axvline(unclosed_gaps['days_since_gap'].mean(), color='red', linestyle='--',
                label=f"Mean: {unclosed_gaps['days_since_gap'].mean():.1f} days")
    ax3.set_xlabel('Days Since Gap Creation')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Age of Unclosed Gaps')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Distance to closure
    ax4 = fig.add_subplot(gs[2, 0])
    unclosed_gaps['distance_to_close'].abs().hist(bins=15, ax=ax4, edgecolor='black', alpha=0.7, color='gold')
    ax4.axvline(unclosed_gaps['distance_to_close'].abs().mean(), color='red', linestyle='--',
                label=f"Mean: ${unclosed_gaps['distance_to_close'].abs().mean():,.2f}")
    ax4.set_xlabel('Distance to Closure (USD, absolute)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distance to Gap Closure')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Gap size vs days since gap
    ax5 = fig.add_subplot(gs[2, 1])
    colors = ['red' if x == 'up' else 'green' for x in unclosed_gaps['gap_direction']]
    scatter = ax5.scatter(unclosed_gaps['days_since_gap'], unclosed_gaps['gap_size'].abs(),
                         c=colors, s=100, alpha=0.6, edgecolors='black', linewidth=1)
    ax5.set_xlabel('Days Since Gap Creation')
    ax5.set_ylabel('Gap Size (USD, absolute)')
    ax5.set_title('Gap Size vs Age')
    ax5.grid(True, alpha=0.3)
    
    # Add legend for direction
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.6, label='Upward Gap'),
        Patch(facecolor='green', alpha=0.6, label='Downward Gap')
    ]
    ax5.legend(handles=legend_elements)
    
    plt.suptitle('Unclosed CME Gaps Analysis', fontsize=16, fontweight='bold', y=0.995)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Unclosed gaps visualization saved to {save_path}")
    else:
        plt.show()


def main():
    """Main function to generate unclosed gaps report."""
    parser = argparse.ArgumentParser(description='Generate detailed report on unclosed CME gaps')
    parser.add_argument('--start-date', type=str, default=None,
                       help='Start date in YYYY-MM-DD format (default: 3 years ago)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date in YYYY-MM-DD format (default: now)')
    parser.add_argument('--exchange', type=str, default='binance',
                       choices=['binance', 'coinbase'],
                       help='Exchange to use for data (default: binance)')
    parser.add_argument('--local-tz', type=str, default='America/Chicago',
                       help='Local timezone for CME hours (default: America/Chicago)')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for plots (default: output)')
    parser.add_argument('--save-csv', action='store_true',
                       help='Save unclosed gaps to CSV')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("UNCLOSED CME GAPS REPORT GENERATOR")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Start Date: {args.start_date or '3 years ago'}")
    print(f"  End Date: {args.end_date or 'now'}")
    print(f"  Exchange: {args.exchange}")
    print(f"  Timezone: {args.local_tz}")
    print()
    
    # Step 1: Download BTC data
    print("Step 1: Downloading Bitcoin price data...")
    try:
        df = download_btc_candles(
            start_date=args.start_date,
            end_date=args.end_date,
            interval='1h',
            exchange=args.exchange
        )
        print(f"✓ Downloaded {len(df)} hourly candles")
    except Exception as e:
        print(f"✗ Error downloading data: {e}")
        return 1
    
    # Step 2: Detect CME gaps
    print("\nStep 2: Detecting CME gaps...")
    try:
        gaps_df = detect_cme_gaps(df, local_tz=args.local_tz)
        print(f"✓ Detected {len(gaps_df)} CME gaps")
    except Exception as e:
        print(f"✗ Error detecting gaps: {e}")
        return 1
    
    if gaps_df.empty:
        print("No gaps detected. Exiting.")
        return 0
    
    # Step 3: Find gap closures
    print("\nStep 3: Finding gap closures...")
    try:
        gaps_df = find_gap_closures(df, gaps_df)
        closed_count = gaps_df['is_closed'].sum()
        unclosed_count = (~gaps_df['is_closed']).sum()
        print(f"✓ Analyzed gap closures: {closed_count} closed, {unclosed_count} unclosed")
    except Exception as e:
        print(f"✗ Error finding closures: {e}")
        return 1
    
    # Step 4: Calculate unclosed gap statistics
    print("\nStep 4: Calculating unclosed gap statistics...")
    try:
        unclosed_stats = calculate_unclosed_gap_statistics(gaps_df, df)
        print_unclosed_gap_report(unclosed_stats)
    except Exception as e:
        print(f"✗ Error calculating statistics: {e}")
        return 1
    
    # Step 5: Generate visualizations
    print("\nStep 5: Generating visualizations...")
    try:
        plot_unclosed_gaps_detailed(
            df, gaps_df, unclosed_stats,
            save_path=str(output_dir / 'unclosed_gaps_report.png')
        )
        print("✓ Visualization generated")
    except Exception as e:
        print(f"✗ Error generating visualizations: {e}")
        return 1
    
    # Step 6: Save CSV if requested
    if args.save_csv and unclosed_stats.get('total_unclosed', 0) > 0:
        csv_path = output_dir / 'unclosed_gaps.csv'
        unclosed_stats['unclosed_gaps_df'].to_csv(csv_path, index=False)
        print(f"\n✓ Unclosed gaps saved to {csv_path}")
    
    print("\n" + "="*70)
    print("Report generation complete!")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

