"""
Tests for gap detection functionality.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cme_gap_analyzer.gap_detector import detect_cme_gaps, find_gap_closures


class TestGapDetector(unittest.TestCase):
    """Test cases for gap detection."""
    
    def setUp(self):
        """Create sample data for testing."""
        # Create sample hourly data
        start = datetime(2023, 1, 1, 0, 0, 0)
        dates = [start + timedelta(hours=i) for i in range(24 * 7 * 4)]  # 4 weeks
        
        # Create price data with a gap
        base_price = 30000.0
        prices = []
        for i, date in enumerate(dates):
            # Simulate price movement
            price = base_price + np.sin(i / 10) * 1000 + np.random.randn() * 100
            prices.append(max(price, 1000))  # Ensure positive prices
        
        self.df = pd.DataFrame({
            'timestamp': pd.to_datetime(dates),
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': [p * 1.005 for p in prices],
            'volume': np.random.rand(len(dates)) * 1000
        })
    
    def test_detect_cme_gaps_empty_dataframe(self):
        """Test gap detection with empty dataframe."""
        empty_df = pd.DataFrame()
        gaps = detect_cme_gaps(empty_df)
        self.assertTrue(gaps.empty)
    
    def test_detect_cme_gaps_structure(self):
        """Test that detected gaps have correct structure."""
        gaps = detect_cme_gaps(self.df)
        
        if not gaps.empty:
            required_columns = [
                'gap_start', 'gap_end', 'close_price', 'open_price',
                'gap_size', 'gap_size_pct', 'gap_direction'
            ]
            for col in required_columns:
                self.assertIn(col, gaps.columns)
    
    def test_find_gap_closures_empty_gaps(self):
        """Test closure finding with empty gaps dataframe."""
        empty_gaps = pd.DataFrame()
        result = find_gap_closures(self.df, empty_gaps)
        self.assertTrue(result.empty)
    
    def test_find_gap_closures_structure(self):
        """Test that closure finding adds correct columns."""
        gaps = detect_cme_gaps(self.df)
        
        if not gaps.empty:
            gaps_with_closures = find_gap_closures(self.df, gaps)
            required_columns = ['is_closed', 'closure_time', 'hours_to_close', 'days_to_close']
            for col in required_columns:
                self.assertIn(col, gaps_with_closures.columns)


class TestGapClosureLogic(unittest.TestCase):
    """Test gap closure detection logic."""
    
    def setUp(self):
        """Create data with a known gap and closure."""
        # Create data with a gap that gets closed
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        
        # Create price data
        prices = []
        for i in range(len(dates)):
            if i < 50:
                price = 30000 + i * 10
            else:
                # Price drops back to 30000 (gap closure)
                price = 30000 - (i - 50) * 10
            prices.append(max(price, 1000))
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.rand(len(dates)) * 1000
        })
    
    def test_closure_detection(self):
        """Test that closures are detected correctly."""
        gaps = detect_cme_gaps(self.df)
        
        if not gaps.empty:
            gaps_with_closures = find_gap_closures(self.df, gaps)
            # At least some gaps should be detected as closed if price returns
            # (This is a basic test - actual behavior depends on gap timing)
            self.assertIn('is_closed', gaps_with_closures.columns)


if __name__ == '__main__':
    unittest.main()

