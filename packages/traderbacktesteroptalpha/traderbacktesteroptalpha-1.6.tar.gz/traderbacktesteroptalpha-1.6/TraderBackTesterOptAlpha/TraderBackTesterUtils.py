import swifter
import warnings
import datetime
import numpy as np
import pandas as pd
from typing import Any

class TraderBackTesterUtils:
    def __init__(self, files_path:str) -> None:
        self.files_path = files_path
        self.all = pd.read_csv(self.files_path + 'all.csv').name.to_list()
        today_dt = datetime.datetime.now().date()
        self.angel_tokens = pd.read_csv(self.files_path + 'angel_tokens.csv', low_memory=False)
        self.angel_tokens.expiry = self.angel_tokens.expiry.str[:-4] + self.angel_tokens.expiry.str[-2:]
        self.angel_tokens = self.angel_tokens[(pd.to_datetime(self.angel_tokens.expiry).dt.date>=today_dt)]
        self.angel_tokens.reset_index(drop=True, inplace=True)
        self.index_ = ['BANKNIFTY', 'NIFTY', 'MIDCPNIFTY']
        warnings.filterwarnings('ignore')

    def get_delta_strike_def(self, name:str) -> pd.DataFrame:
        tokens=self.angel_tokens
        tokens = tokens[tokens.name.isin(self.index_ + self.all)]
        tokens = tokens[~tokens.strike.isin([1, -1, 0])]
        tokens['expiry'] = pd.to_datetime(tokens.expiry).astype(str)
        tokens['strike'] = tokens.strike/100

        strk = pd.DataFrame(sorted(tokens[(tokens.name == name)].strike.drop_duplicates().to_list()), columns=['strikes'])
        strk['shift_strikes'] = strk.strikes.shift(-1)
        strk['strikes_def'] = strk.shift_strikes - strk.strikes
        strk.dropna(inplace=True)
        strk = pd.DataFrame(strk.strikes_def.value_counts())
        strk['strike'] = strk.index
        strk.reset_index(drop=True,inplace=True)
        return strk

    def round_to(self, row:Any, num_column:str = 'open', precision_column_val:Any = .05) -> float:
        ''' Round given number to nearsest tick size which is .05 in FNO
            Source: https://stackoverflow.com/questions/4265546/python-round-to-nearest-05

            Parameters
            ----------
                row: int/float/Series - 12569.67 or Series with columns __ num_column, optional __ precision_column_val
                num_column: str - 'date' Column name to round
                precision_column_val: float, int, str 100, 2.5 or 'roundvalue' tick_size of the item or  Column name contaning tick_size

        '''
        if type(row) in [int, float, np.float64, np.float32, np.float16, np.int8, np.int16, np.int32, np.int64, str]:
            n = row
        else:
            n = row[num_column]

        if type(precision_column_val)==str:
            if type(row) in [int, float, np.float64, np.float32, np.float16, np.int8, np.int16, np.int32, np.int64, str]:
                precision = .05
            else:
                precision = row[precision_column_val]
        else:
            precision = precision_column_val

        n = float(n)
        correction = 0.5 if n >= 0 else -0.5
        return round(int( n/precision+correction ) * precision, 2)

    def get_strike(self, x:Any, num_column:str = 'open', precision_column_val:Any = .05) -> Any:
        '''
        n: float, int, DataFrame
            number to round to nearsest tick size or DataFrame contaning numbers to round to nearsest tick size
        num_column: str - Column name to round
        precision_column_val: float, int, str
            tick_size of the item or  Column name contaning tick_size
        '''
        if type(x) in [int, float, np.float64, np.float32, np.float16, np.int8, np.int16, np.int32, np.int64, str]:
            return self.round_to(x, num_column, precision_column_val)
        elif type(precision_column_val)!=str:
            return ((x[num_column] / precision_column_val).round() * precision_column_val).round(2)
        else:
            return x.swifter.apply(self.round_to, args = (num_column, precision_column_val,), axis = 1)

    def exp_cal(self, row:Any, x_org:pd.DataFrame, dat:str = 'date', nxt_exp:Any = 0, montly:Any = False) -> str:
        '''
        row: str/Series - '2022-04-20' or Series with columns __ dat, optional __ nxt_exp, montly
        x_org: DataFrame - Original DataFrame
        dat: str - date column name with dates in '2022-04-20' formate default 'date'
        nxt_exp: int/str - 1,2,3 or column name with int gives next expiry of the order default 0
        montly: bool/str - True/False or column name with bool gives monthly expiry or weekly expiry default False
        '''
        try:
            if type(row)==str:
                date = row
            else:
                date = row[dat]

            if type(nxt_exp)==str:
                if type(row)==str:
                    next_exp = 0
                else:
                    next_exp = row[nxt_exp]
            else:
                next_exp = nxt_exp

            if type(montly)==str:
                if type(row)==str:
                    monthly = False
                else:
                    monthly = row[montly]
            else:
                monthly = montly

            tokens = self.angel_tokens[(self.angel_tokens.name == x_org.ticker.iloc[0])&(self.angel_tokens.expiry!='')]

            exp_day = 3

            if (date >= '2025-09-01'): exp_day = 1

            if (x_org.ticker.iloc[0] == 'BANKNIFTY') and (date >= '2024-03-01') and (date <= '2024-12-31'): exp_day = 2

            if not monthly:
                if pd.to_datetime(date).dayofweek <= exp_day:
                    days_to_add  = (exp_day - pd.to_datetime(date).dayofweek) + next_exp*7
                else:
                    days_to_add  = (exp_day + 7 - pd.to_datetime(date).dayofweek) + next_exp*7
                x = pd.to_datetime(date).date() + datetime.timedelta(days=days_to_add)

                expiries = pd.DataFrame(pd.to_datetime(tokens.expiry).dt.date.unique(), columns=['exp'])
                expiries['days'] = abs(expiries.exp - x)
                expiries.sort_values(['days'], inplace=True)

                while str(x) not in x_org.date.to_list():
                    if expiries.iloc[0].days.days<=2:
                        x = str(expiries.iloc[0].exp)
                        break
                    x = x - datetime.timedelta(days=1)
                return str(x)
            else:
                _date_ = date

                x = pd.to_datetime(_date_).replace(day=pd.to_datetime(_date_).days_in_month)
                _date_ = str(pd.to_datetime(x).date() + datetime.timedelta(days=1))
                if x.dayofweek > exp_day:
                    to_sub = x.dayofweek - exp_day
                elif x.dayofweek < exp_day:
                    to_sub = x.dayofweek - exp_day + 7
                else:
                    to_sub = 0
                x = x.date() - datetime.timedelta(days=to_sub)
                x = pd.to_datetime(x)

                if str(x) < date: next_exp = next_exp + 1 # Check if current month expiry is less than current date if so increase next_exp by 1

                for i in range(next_exp):
                    x = pd.to_datetime(_date_).replace(day=pd.to_datetime(_date_).days_in_month)
                    _date_ = str(pd.to_datetime(x).date() + datetime.timedelta(days=1))
                if x.dayofweek > exp_day:
                    to_sub = x.dayofweek - exp_day
                elif x.dayofweek < exp_day:
                    to_sub = x.dayofweek - exp_day + 7
                else:
                    to_sub = 0
                x = x.date() - datetime.timedelta(days=to_sub)

                expiries = pd.DataFrame(pd.to_datetime(tokens.expiry).dt.date.unique(), columns=['exp'])
                expiries['days'] = abs(expiries.exp - x)
                expiries.sort_values(['days'], inplace=True)

                while str(x) not in x_org.date.to_list():
                    if expiries.iloc[0].days.days<=2:
                        x = str(expiries.iloc[0].exp)
                        break
                    x = x - datetime.timedelta(days=1)
                return str(x)
        except Exception as e: pass

    def get_exp(self, x:Any, x_org:pd.DataFrame, dat:str = 'date', nxt_exp:Any = 0, montly:bool = False) -> Any:
        '''
        x: str/DataFrame - '2022-04-20' or Dataframe with columns __ dat, optional __ nxt_exp, montly
        x_org: DataFrame - Original DataFrame 
        dat: str - date column name with dates in '2022-04-20' formate default 'date'
        nxt_exp: int/str - 1,2,3 or column name with int gives next expiry of the order default 0
        montly: bool/str - True/False or column name with bool gives monthly expiry or weekly expiry default False
        '''
        if type(x)==str:
            return self.exp_cal(x, x_org, dat, nxt_exp, montly)
        else:
            return x.swifter.apply(self.exp_cal, args=(x_org, dat, nxt_exp, montly), axis = 1)

    def get_lot(self, name:str) -> pd.DataFrame:
        tokens=self.angel_tokens
        tokens = tokens[tokens.name.isin(self.index_ + self.all)]
        tokens = tokens[~tokens.strike.isin([1, -1, 0])]
        tokens['expiry'] = pd.to_datetime(tokens.expiry).astype(str)
        tokens['strike'] = tokens.strike/100

        return tokens[(tokens.name == name)].lotsize.drop_duplicates().iloc[0]

    def add_n_lot_only(self, data:pd.DataFrame, ticker_column:str, column_name_to_create:str) -> pd.DataFrame:
        data = data.copy()
        data[column_name_to_create] = self.get_lot(data[ticker_column].iloc[0])
        return data

    def is_holiday(self, date:str = '') -> bool:
        ''' Returns True if today/given date is a market holiday else False.
        
            Parameters
            ----------
            date: datetime
                date example datetime.datetime(2022,1,26).date()
            
            Returns
            -------
            boolean: True/False
                True if holiday else False
        '''
        df = pd.read_excel(self.files_path + 'nse_holidays.xlsx')
        df.Date = pd.to_datetime(df.Date)
        if date == '':
            return (datetime.datetime.now().date() in list(df.Date.dt.date)) or (datetime.datetime.now().date().isoweekday() in [6, 7])
        else: return date in list(df.Date.dt.date) or (date.isoweekday() in [6, 7])

def update_files(files_path:str, file_server_url:str) -> None:
    try:
        file_url = file_server_url +'send_file?file_name=nse_holidays.xlsx'
        data = pd.read_excel(file_url)
        del data['Unnamed: 0']
        data.to_excel(files_path + 'nse_holidays.xlsx')
    except: print('Unable to download nse_holidays')

    try:
        file_url = file_server_url +'send_file?file_name=angel_tokens.csv'
        pd.read_csv(file_url, low_memory=False).to_csv(files_path + 'angel_tokens.csv', index = False)
    except: print('Unable to download angel_tokens')

    try:
        file_url = file_server_url +'send_file?file_name=all.csv'
        pd.read_csv(file_url, low_memory=False).to_csv(files_path + 'all.csv', index = False)
    except: print('Unable to download all')