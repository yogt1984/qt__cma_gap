"""
Main script to run CME gap analysis.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path (main.py is in src/cme_gap_analyzer/, so parent.parent is src/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from cme_gap_analyzer.data_downloader import download_btc_candles
from cme_gap_analyzer.gap_detector import detect_cme_gaps, find_gap_closures
from cme_gap_analyzer.statistics import calculate_gap_statistics, print_statistics
from cme_gap_analyzer.visualizations import (
    plot_gap_statistics,
    plot_price_action_with_gaps,
    plot_closure_analysis
)


def main():
    """Main function to run the CME gap analysis."""
    parser = argparse.ArgumentParser(description='Analyze CME gaps in Bitcoin price data')
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
                       help='Output directory for plots and data (default: output)')
    parser.add_argument('--save-data', action='store_true',
                       help='Save downloaded data and gap results to CSV')
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip generating plots')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("CME GAP ANALYZER")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Start Date: {args.start_date or '3 years ago'}")
    print(f"  End Date: {args.end_date or 'now'}")
    print(f"  Exchange: {args.exchange}")
    print(f"  Timezone: {args.local_tz}")
    print(f"  Output Directory: {output_dir}")
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
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Error downloading data: {e}")
        return 1
    
    if args.save_data:
        data_path = output_dir / 'btc_price_data.csv'
        df.to_csv(data_path, index=False)
        print(f"✓ Saved price data to {data_path}")
    
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
        print(f"✓ Analyzed gap closures: {closed_count}/{len(gaps_df)} gaps closed")
    except Exception as e:
        print(f"✗ Error finding closures: {e}")
        return 1
    
    if args.save_data:
        gaps_path = output_dir / 'cme_gaps.csv'
        gaps_df.to_csv(gaps_path, index=False)
        print(f"✓ Saved gap data to {gaps_path}")
    
    # Step 4: Calculate statistics
    print("\nStep 4: Calculating statistics...")
    try:
        stats = calculate_gap_statistics(gaps_df)
        print_statistics(stats)
    except Exception as e:
        print(f"✗ Error calculating statistics: {e}")
        return 1
    
    # Step 5: Generate visualizations
    if not args.no_plots:
        print("\nStep 5: Generating visualizations...")
        try:
            plot_gap_statistics(gaps_df, save_path=str(output_dir / 'gap_statistics.png'))
            plot_price_action_with_gaps(df, gaps_df, save_path=str(output_dir / 'price_action_with_gaps.png'))
            plot_closure_analysis(gaps_df, save_path=str(output_dir / 'closure_analysis.png'))
            print("✓ All visualizations generated")
        except Exception as e:
            print(f"✗ Error generating visualizations: {e}")
            return 1
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

