"""
Module for detecting CME gaps in Bitcoin price data.

CME (Chicago Mercantile Exchange) closes on Friday at 4:00 PM CT (Central Time)
and reopens on Sunday at 5:00 PM CT. Gaps occur when the price at CME close
differs from the price when it reopens.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
import pytz


def detect_cme_gaps(df: pd.DataFrame, local_tz: str = "America/Chicago") -> pd.DataFrame:
    """
    Detect CME gaps in hourly Bitcoin price data.
    
    CME closes: Friday 4:00 PM CT
    CME opens: Sunday 5:00 PM CT
    
    Args:
        df: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        local_tz: Timezone string (default: 'America/Chicago' for CT)
    
    Returns:
        DataFrame with detected gaps, including:
        - gap_start: CME close timestamp
        - gap_end: CME open timestamp
        - close_price: Price at CME close
        - open_price: Price at CME open
        - gap_size: Absolute gap size
        - gap_size_pct: Gap size as percentage
        - gap_direction: 'up' or 'down'
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure timestamp is timezone-aware
    if df['timestamp'].dt.tz is None:
        df = df.copy()
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    else:
        df = df.copy()
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    
    # Convert to local timezone
    local_tz_obj = pytz.timezone(local_tz)
    df['local_time'] = df['timestamp'].dt.tz_convert(local_tz_obj)
    
    # Find all Fridays and Sundays
    df['day_of_week'] = df['local_time'].dt.dayofweek  # 4 = Friday, 6 = Sunday
    df['hour'] = df['local_time'].dt.hour
    df['date'] = df['local_time'].dt.date
    
    gaps = []
    
    # Find all Friday 4 PM closes
    friday_closes = df[
        (df['day_of_week'] == 4) & 
        (df['hour'] == 16)
    ].copy()
    
    if friday_closes.empty:
        return pd.DataFrame()
    
    friday_closes = friday_closes.sort_values('local_time')
    
    # For each Friday close, find the corresponding Sunday 5 PM open
    for idx, friday_close in friday_closes.iterrows():
        friday_time = friday_close['local_time']
        next_sunday_time = friday_time + timedelta(days=2, hours=1)  # Sunday 5 PM
        
        # Find the closest Sunday 5 PM candle
        sunday_opens = df[
            (df['day_of_week'] == 6) & 
            (df['hour'] == 17) &
            (df['local_time'] > friday_time)
        ].copy()
        
        if sunday_opens.empty:
            continue
        
        # Get the first Sunday 5 PM after this Friday
        sunday_open = sunday_opens.iloc[0]
        
        close_price = friday_close['close']
        open_price = sunday_open['open']
        
        # Only record if there's actually a gap
        if abs(close_price - open_price) > 0.01:  # Minimum gap threshold
            gap_size = open_price - close_price
            gap_size_pct = (gap_size / close_price) * 100
            gap_direction = 'up' if gap_size > 0 else 'down'
            
            gaps.append({
                'gap_start': friday_close['timestamp'],
                'gap_end': sunday_open['timestamp'],
                'close_price': close_price,
                'open_price': open_price,
                'gap_size': gap_size,
                'gap_size_pct': gap_size_pct,
                'gap_direction': gap_direction,
                'friday_date': friday_time.date(),
                'sunday_date': sunday_open['local_time'].date()
            })
    
    if not gaps:
        return pd.DataFrame()
    
    gaps_df = pd.DataFrame(gaps)
    gaps_df = gaps_df.sort_values('gap_start').reset_index(drop=True)
    
    return gaps_df


def find_gap_closures(
    df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    tolerance: float = 0.001
) -> pd.DataFrame:
    """
    Find when each CME gap was closed (price returned to closing level).
    
    Args:
        df: Original price DataFrame
        gaps_df: DataFrame with detected gaps
        tolerance: Percentage tolerance for considering gap closed (default: 0.1%)
    
    Returns:
        gaps_df with additional columns:
        - is_closed: Boolean indicating if gap was closed
        - closure_time: Timestamp when gap was closed (if closed)
        - hours_to_close: Hours between gap creation and closure
        - days_to_close: Days between gap creation and closure
    """
    if gaps_df.empty:
        return gaps_df
    
    gaps_df = gaps_df.copy()
    gaps_df['is_closed'] = False
    gaps_df['closure_time'] = pd.NaT
    gaps_df['hours_to_close'] = np.nan
    gaps_df['days_to_close'] = np.nan
    
    # Ensure df timestamps are timezone-aware
    if df['timestamp'].dt.tz is None:
        df_work = df.copy()
        df_work['timestamp'] = df_work['timestamp'].dt.tz_localize('UTC')
    else:
        df_work = df.copy()
        df_work['timestamp'] = df_work['timestamp'].dt.tz_convert('UTC')
    
    df_work = df_work.sort_values('timestamp').reset_index(drop=True)
    
    for idx, gap in gaps_df.iterrows():
        gap_end_time = gap['gap_end']
        close_price = gap['close_price']
        
        # Find all candles after gap end
        future_candles = df_work[df_work['timestamp'] > gap_end_time].copy()
        
        if future_candles.empty:
            continue
        
        # Check if price crossed the close price
        # For upward gaps: price needs to go below close_price
        # For downward gaps: price needs to go above close_price
        
        if gap['gap_direction'] == 'up':
            # Upward gap: look for price going below close_price
            mask = future_candles['low'] <= close_price * (1 + tolerance)
        else:
            # Downward gap: look for price going above close_price
            mask = future_candles['high'] >= close_price * (1 - tolerance)
        
        closed_candles = future_candles[mask]
        
        if not closed_candles.empty:
            closure_time = closed_candles.iloc[0]['timestamp']
            time_diff = closure_time - gap_end_time
            
            gaps_df.at[idx, 'is_closed'] = True
            gaps_df.at[idx, 'closure_time'] = closure_time
            gaps_df.at[idx, 'hours_to_close'] = time_diff.total_seconds() / 3600
            gaps_df.at[idx, 'days_to_close'] = time_diff.total_seconds() / 86400
    
    return gaps_df

