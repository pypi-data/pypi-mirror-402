# traderbacktesteroptalpha

This Python script provides three main functionalities:
1. Updating essential files from a server (`update_files` function).
2. Utility functions for backtesting and trading strategies (`TraderBackTesterUtils` class).
3. Data manipulation functions for backtesting and trading strategies (`TraderBackTesterDM` class).

## Requirements

This script requires the following libraries:

- pandas_ta==0.3.14b0
- swifter==1.3.4
- openpyxl==3.1.2
- ta==0.10.2
- pandas==1.5.3
- numpy==1.23.5

To install these dependencies, use the following command:
```bash
pip install pandas_ta==0.3.14b0 swifter==1.3.4 openpyxl==3.1.2 ta==0.10.2 pandas==1.5.3 numpy==1.23.5  
```

## Usage

### 1. File Updater (`update_files` function)
The `update_files` function downloads and saves three files required for backtesting:
- `nse_holidays.xlsx`: A list of market holidays.
- `angel_tokens.csv`: Token data for various trading instruments.
- `all.csv`: A list of available instruments.

To update these files, call the function:
```python
update_files(files_path='path/to/save/files/', file_server_url='http://your_server_url/')
```

### 2. TraderBackTesterUtils Class
This class provides multiple utility methods for trading and backtesting. Initialize it with the path where required files are stored.

#### Initialization
```python
trader_backtester_utils = TraderBackTesterUtils(files_path='path/to/files/')
```

### Methods

#### `get_delta_strike_def(name: str) -> pd.DataFrame`
Returns strike price details for a given instrument, calculating the differences between consecutive strikes.

#### `round_to(row: Any, num_column: str = 'open', precision_column_val: Any = .05) -> float`
Rounds a given value to the nearest tick size (default: 0.05).

#### `get_strike(x: Any, num_column: str = 'open', precision_column_val: Any = .05) -> Any`
Rounding method that applies `round_to` on a DataFrame using `swifter` for parallel processing.

#### `exp_cal(row: Any, x_org: pd.DataFrame, dat: str = 'date', nxt_exp: Any = 0, montly: Any = False) -> str`
Calculates the next expiry date for an instrument. Determines weekly or monthly expiry based on input parameters.

#### `get_exp(x: Any, x_org: pd.DataFrame, dat: str = 'date', nxt_exp: Any = 0, montly: bool = False) -> Any`
Uses `exp_cal` to calculate expiries for a DataFrame.

#### `get_lot(name: str) -> pd.DataFrame`
Fetches lot size for a specified instrument name.

#### `add_n_lot_only(data: pd.DataFrame, ticker_column: str, exp_colummn_name: str, column_name_to_create: str) -> pd.DataFrame`
Adds a new column with lot sizes based on the ticker and expiry date.

#### `is_holiday(date: str = '') -> bool`
Checks if a given date is a market holiday. Defaults to checking today's date.

### Example Usage
```python
# Initializing
trader_backtester_utils = TraderBackTesterUtils(files_path='path/to/files/')

# Getting delta strike definitions
delta_strike = trader_backtester_utils.get_delta_strike_def(name='NIFTY')

# Rounding example
rounded_value = trader_backtester_utils.round_to(12569.67)

# Calculating expiry
expiry_date = trader_backtester_utils.get_exp(x='2022-04-20', x_org=your_dataframe)

# Adding lot sizes to DataFrame
updated_data = trader_backtester_utils.add_n_lot_only(data=your_dataframe, ticker_column='ticker', exp_colummn_name='expiry', column_name_to_create='lot_size')
```

### 3. TraderBackTesterDM Class
This class provides multiple data manipulation methods for trading and backtesting

#### Initialization
```python
trader_backtester_dm = TraderBackTesterDM()
```