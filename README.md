# CME Gap Analyzer

A Python tool to analyze CME (Chicago Mercantile Exchange) gaps in Bitcoin price data. CME gaps occur when the Bitcoin futures market closes on Friday at 4:00 PM CT and reopens on Sunday at 5:00 PM CT, creating price gaps that may or may not be filled.

## Features

- **Download Historical Data**: Download Bitcoin price data from Binance or Coinbase
- **Gap Detection**: Automatically detect CME gaps based on market hours
- **Closure Tracking**: Track when gaps are closed (price returns to closing level)
- **Statistical Analysis**: Comprehensive statistics on gap sizes, closure rates, and timing
- **Visualizations**: Multiple plots showing gap statistics, price action, and closure analysis

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
make install
```

Or manually:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

Run the full analysis:

```bash
make run
```

Or with custom options:

```bash
python -m cme_gap_analyzer.main --start-date 2022-01-01 --end-date 2024-01-01
```

Available options:
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--exchange`: Exchange to use (`binance` or `coinbase`, default: `binance`)
- `--local-tz`: Timezone for CME hours (default: `America/Chicago`)
- `--output-dir`: Output directory for plots and data (default: `output`)
- `--save-data`: Save downloaded data and gap results to CSV
- `--no-plots`: Skip generating plots

### Jupyter Notebook

Launch Jupyter notebook for interactive analysis:

```bash
make notebook
```

Then open `notebooks/cme_gap_analysis.ipynb`

### Python API

```python
from cme_gap_analyzer.data_downloader import download_btc_candles
from cme_gap_analyzer.gap_detector import detect_cme_gaps, find_gap_closures
from cme_gap_analyzer.statistics import calculate_gap_statistics, print_statistics
from cme_gap_analyzer.visualizations import plot_gap_statistics, plot_price_action_with_gaps

# Download data
df = download_btc_candles(start_date='2022-01-01', interval='1h')

# Detect gaps
gaps_df = detect_cme_gaps(df)

# Find closures
gaps_df = find_gap_closures(df, gaps_df)

# Calculate statistics
stats = calculate_gap_statistics(gaps_df)
print_statistics(stats)

# Visualize
plot_gap_statistics(gaps_df)
plot_price_action_with_gaps(df, gaps_df)
```

## Project Structure

```
.
├── src/
│   └── cme_gap_analyzer/
│       ├── __init__.py
│       ├── data_downloader.py    # Download BTC price data
│       ├── gap_detector.py        # Detect CME gaps
│       ├── statistics.py          # Calculate statistics
│       ├── visualizations.py      # Create plots
│       └── main.py                # Main script
├── tests/
│   ├── __init__.py
│   ├── test_gap_detector.py
│   └── test_statistics.py
├── notebooks/
│   └── cme_gap_analysis.ipynb    # Jupyter notebook
├── output/                        # Generated plots and data
├── requirements.txt
├── Makefile
└── README.md
```

## Testing

Run all tests:

```bash
make test
```

Or with pytest:

```bash
pytest tests/ -v
```

## Output

The analysis generates:

1. **Statistics**: Printed to console and saved to CSV (if `--save-data` is used)
2. **Plots**:
   - `gap_statistics.png`: Distribution and trends of gap sizes
   - `price_action_with_gaps.png`: Bitcoin price chart with gaps highlighted
   - `closure_analysis.png`: Detailed closure analysis

## CME Gap Explanation

CME Bitcoin futures close on Friday at 4:00 PM Central Time (CT) and reopen on Sunday at 5:00 PM CT. During this time, Bitcoin continues trading on spot exchanges. When the futures market reopens, if the price differs from Friday's close, a "gap" is created. These gaps often get "filled" when price returns to the Friday closing level.

## License

This project is provided as-is for educational and research purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

