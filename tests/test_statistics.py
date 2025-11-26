"""
Tests for statistics calculation.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cme_gap_analyzer.statistics import calculate_gap_statistics


class TestStatistics(unittest.TestCase):
    """Test cases for statistics calculation."""
    
    def setUp(self):
        """Create sample gap data."""
        dates = pd.date_range('2023-01-01', periods=10, freq='W')
        
        self.gaps_df = pd.DataFrame({
            'gap_start': dates,
            'gap_end': dates + timedelta(days=2),
            'close_price': [30000 + i * 100 for i in range(10)],
            'open_price': [30100 + i * 100 for i in range(10)],
            'gap_size': [100] * 10,
            'gap_size_pct': [100 / (30000 + i * 100) * 100 for i in range(10)],
            'gap_direction': ['up'] * 10,
            'is_closed': [True] * 5 + [False] * 5,
            'closure_time': [dates[i] + timedelta(days=3) if i < 5 else pd.NaT for i in range(10)],
            'hours_to_close': [72 if i < 5 else np.nan for i in range(10)],
            'days_to_close': [3 if i < 5 else np.nan for i in range(10)]
        })
    
    def test_calculate_statistics_empty(self):
        """Test statistics with empty dataframe."""
        empty_df = pd.DataFrame()
        stats = calculate_gap_statistics(empty_df)
        self.assertEqual(stats['total_gaps'], 0)
        self.assertIn('message', stats)
    
    def test_calculate_statistics_basic(self):
        """Test basic statistics calculation."""
        stats = calculate_gap_statistics(self.gaps_df)
        
        self.assertEqual(stats['total_gaps'], 10)
        self.assertEqual(stats['closed_gaps'], 5)
        self.assertEqual(stats['open_gaps'], 5)
        self.assertEqual(stats['closure_rate'], 50.0)
    
    def test_calculate_statistics_gap_sizes(self):
        """Test gap size statistics."""
        stats = calculate_gap_statistics(self.gaps_df)
        
        self.assertIn('avg_gap_size', stats)
        self.assertIn('median_gap_size', stats)
        self.assertIn('std_gap_size', stats)
        self.assertGreater(stats['avg_gap_size'], 0)
    
    def test_calculate_statistics_closure_times(self):
        """Test closure time statistics."""
        stats = calculate_gap_statistics(self.gaps_df)
        
        self.assertIn('avg_hours_to_close', stats)
        self.assertIn('avg_days_to_close', stats)
        self.assertFalse(pd.isna(stats['avg_hours_to_close']))
        self.assertEqual(stats['avg_days_to_close'], 3.0)
    
    def test_calculate_statistics_directions(self):
        """Test direction-based statistics."""
        stats = calculate_gap_statistics(self.gaps_df)
        
        self.assertEqual(stats['up_gaps'], 10)
        self.assertEqual(stats['down_gaps'], 0)
        self.assertIn('up_gap_closure_rate', stats)
        self.assertIn('down_gap_closure_rate', stats)


if __name__ == '__main__':
    unittest.main()

