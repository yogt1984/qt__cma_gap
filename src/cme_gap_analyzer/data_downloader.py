"""
Module for downloading Bitcoin historical price data.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
import time


def download_btc_candles(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1h",
    exchange: str = "binance"
) -> pd.DataFrame:
    """
    Download Bitcoin historical candle data.
    
    Args:
        start_date: Start date in format 'YYYY-MM-DD'. If None, downloads from earliest available.
        end_date: End date in format 'YYYY-MM-DD'. If None, downloads until now.
        interval: Candle interval (default: '1h' for hourly)
        exchange: Exchange to use ('binance' or 'coinbase')
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    if exchange == "binance":
        return _download_from_binance(start_date, end_date, interval)
    elif exchange == "coinbase":
        return _download_from_coinbase(start_date, end_date, interval)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")


def _download_from_binance(
    start_date: Optional[str],
    end_date: Optional[str],
    interval: str
) -> pd.DataFrame:
    """Download data from Binance API."""
    base_url = "https://api.binance.com/api/v3/klines"
    symbol = "BTCUSDT"
    
    # Convert interval to Binance format
    interval_map = {
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }
    binance_interval = interval_map.get(interval, "1h")
    
    # Convert dates to timestamps
    if start_date:
        start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    else:
        # Default to 3 years ago
        start_ts = int((datetime.now() - timedelta(days=3*365)).timestamp() * 1000)
    
    if end_date:
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
    else:
        end_ts = int(datetime.now().timestamp() * 1000)
    
    all_data = []
    current_start = start_ts
    limit = 1000  # Binance limit per request
    
    print(f"Downloading BTC data from Binance...")
    print(f"Start: {pd.Timestamp(start_ts, unit='ms')}, End: {pd.Timestamp(end_ts, unit='ms')}")
    
    while current_start < end_ts:
        params = {
            "symbol": symbol,
            "interval": binance_interval,
            "startTime": current_start,
            "endTime": end_ts,
            "limit": limit
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            all_data.extend(data)
            
            # Update start time for next batch
            current_start = data[-1][0] + 1
            
            # Rate limiting
            time.sleep(0.1)
            
            if len(data) < limit:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error downloading data: {e}")
            break
    
    if not all_data:
        raise ValueError("No data downloaded")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    # Convert price columns to float
    price_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in price_cols:
        df[col] = df[col].astype(float)
    
    # Select and rename columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"Downloaded {len(df)} candles")
    return df


def _download_from_coinbase(
    start_date: Optional[str],
    end_date: Optional[str],
    interval: str
) -> pd.DataFrame:
    """Download data from Coinbase API (fallback)."""
    # Coinbase Pro API endpoint
    base_url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
    
    # Convert interval to seconds
    interval_map = {
        "1h": 3600,
        "4h": 14400,
        "1d": 86400
    }
    granularity = interval_map.get(interval, 3600)
    
    if start_date:
        start_ts = pd.Timestamp(start_date)
    else:
        start_ts = datetime.now() - timedelta(days=3*365)
    
    if end_date:
        end_ts = pd.Timestamp(end_date)
    else:
        end_ts = datetime.now()
    
    all_data = []
    current_start = start_ts
    
    print(f"Downloading BTC data from Coinbase...")
    
    while current_start < end_ts:
        params = {
            "start": current_start.isoformat(),
            "end": min(current_start + timedelta(days=300), end_ts).isoformat(),
            "granularity": granularity
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or 'message' in data:
                break
            
            all_data.extend(data)
            current_start += timedelta(days=300)
            time.sleep(0.2)
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading data: {e}")
            break
    
    if not all_data:
        raise ValueError("No data downloaded")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'low', 'high', 'open', 'close', 'volume'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"Downloaded {len(df)} candles")
    return df

