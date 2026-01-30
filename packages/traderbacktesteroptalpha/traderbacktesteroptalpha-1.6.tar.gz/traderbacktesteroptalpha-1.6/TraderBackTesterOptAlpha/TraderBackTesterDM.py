import ta
import warnings
import numpy as np
import pandas as pd
from typing import Any
import pandas_ta as pta

class TraderBackTesterDM:
    def __init__(self) -> None:
        warnings.filterwarnings('ignore')

    def group_on_columns_ops(self, stc_ind_opt_data:pd.DataFrame, column_names:list, operation:str) -> pd.DataFrame:
        '''
        operation on grouped dataframe based on column_names
        stc_ind_opt_data: DataFrame
        operation: str - last, first, max, min, mean
        '''
        stc_ind_opt_data = stc_ind_opt_data.copy()
        columns = []
        for column_name in column_names:
            if stc_ind_opt_data.dtypes[column_name] == 'O':
                columns.append(column_name)
            else:
                columns.append(stc_ind_opt_data[column_name].diff().ne(0).cumsum())
        group_obj = stc_ind_opt_data.groupby(columns)

        to_excute = 'stc_ind_opt_data = group_obj.' + operation + '()'
        locals = {}
        exec(to_excute, {'group_obj':group_obj}, locals)
        stc_ind_opt_data = locals['stc_ind_opt_data']

        for i in column_names:
            if i not in stc_ind_opt_data.columns:stc_ind_opt_data[i] =  stc_ind_opt_data.index.to_frame()[i]
        stc_ind_opt_data.reset_index(inplace=True, drop = True)
        return stc_ind_opt_data

    def join_on_colums(self, x:pd.DataFrame, y:pd.DataFrame, on_:str = 'date', how_:str = 'inner') -> pd.DataFrame:
        return pd.merge(x, y, on = on_, how = how_)

    def features_to_add(self, stc_ind_opt_data:pd.DataFrame, *argv, **kwargs) -> pd.DataFrame:
        '''
        please go through: https://technical-analysis-library-in-python.readthedocs.io/en/latest/index.html
        stc_ind_opt_data: DataFrame
        argv: str TA code - 'ema1:ta.trend.ema_indicator(stc_ind_opt_data.close, fillna = True)', 'rsi:ta.momentum.rsi(stc_ind_opt_data.close, window = 20, fillna = True)', 'week:pd.to_datetime(stc_ind_opt_data.date).dt.dayofweek', 'sum:stc_ind_opt_data.week+stc_ind_opt_data.week'
        '''
        stc_ind_opt_data = stc_ind_opt_data.copy()
        for arg in argv:
            column_name = arg.split(':')[0]
            _cmd_ = arg.split(':')[1]
            stc_ind_opt_data[column_name] = np.nan
            to_excute = 'stc_ind_opt_data' + str([column_name]) + ' = ' + _cmd_
            exec(to_excute, {'pta':pta, 'ta':ta,'stc_ind_opt_data':stc_ind_opt_data,'pd':pd, 'np':np})
        return stc_ind_opt_data

    def resample_stock_data(self, df:pd.DataFrame, timedelta:str = '15T', time_offset:str = '9h15min') -> pd.DataFrame:
        '''
        df: DataFrame dataframe with following formate [ticker	date	time	open	high	low	close	volume]
        timedelta: str - '15T', '3T', '1D', '1W', '1M'.. sampling rate
        '''
        if any(unit in timedelta for unit in ['T', 'H']):
            df_r = df.copy()

            # convert index to datetime
            df_r.index = pd.to_datetime(df_r.date+' '+df_r.time)
            df_r.drop('date', axis='columns', inplace=True)
            df_r.drop('time', axis='columns', inplace=True)

            # sort the index (evidently required by resample())
            df_r = df_r.sort_index()

            aggregation_dict = {
                'volume': 'sum', 
                'open': 'first', 
                'high': 'max', 
                'low': 'min', 
                'close': 'last', 
                'ticker': 'first', 
            }

            fin_stock = (
                df_r.groupby(df_r.index.date, group_keys=False)   # per day
                .apply(lambda x: (
                    x.resample(timedelta, label='left', closed='left', offset=time_offset)
                    .agg(aggregation_dict)
                ))
            )
            fin_stock['date'] = fin_stock.index
            fin_stock['time'] = pd.to_datetime(fin_stock.date).dt.time.astype('str')
            fin_stock['date'] = pd.to_datetime(fin_stock.date).dt.date.astype('str')
        else:
            df_r = df.copy()

            df_r = pd.concat([df_r.iloc[0:1], df_r])
            df_r.date.iloc[0] = '2017-01-02'

            df_r['date_temp'] = df_r.date

            # convert index to datetime
            df_r.index = pd.to_datetime(df_r.date+' '+df_r.time)
            df_r.drop('date', axis='columns', inplace=True)
            df_r.drop('time', axis='columns', inplace=True)

            # sort the index (evidently required by resample())
            df_r = df_r.sort_index()

            aggregation_dict = {
                'volume': 'sum', 
                'open': 'first', 
                'high': 'max', 
                'low': 'min', 
                'close': 'last', 
                'ticker': 'first', 
                'date_temp': 'first', 
            }

            fin_stock =  (df_r
            .resample(timedelta, label='left', closed='left')
            .agg(aggregation_dict)
            )
            fin_stock['date'] = fin_stock.index
            fin_stock['time'] = "09:15:00"
            fin_stock['date'] = pd.to_datetime(fin_stock.date).dt.date.astype('str')
            fin_stock['date'] = fin_stock['date_temp']
            if '2017-01-02' not in df.date.to_list(): fin_stock = fin_stock.drop(fin_stock.index[0])
            fin_stock.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        fin_stock.reset_index(inplace=True)
        fin_stock.drop('index', axis='columns', inplace=True)
        return fin_stock[['ticker','date','time','open','high','low','close','volume']]

    def resample_stock_data_futures(self, df:pd.DataFrame, timedelta:str = '15T', time_offset:str = '9h15min') -> pd.DataFrame:
        '''
        df: DataFrame dataframe with following formate ['ticker', 'date', 'time', 'open', 'high', 'low', 'close', 'volume', 'open_interest', 'expiry_date']
        timedelta: str - '15T', '3T'.. sampling rate
        '''
        df_r = df.copy()

        # convert index to datetime
        df_r.index = pd.to_datetime(df_r.date+' '+df_r.time)
        df_r.drop('date', axis='columns', inplace=True)
        df_r.drop('time', axis='columns', inplace=True)

        # sort the index (evidently required by resample())
        df_r = df_r.sort_index()

        aggregation_dict = {
            'volume': 'sum', 
            'open': 'first', 
            'high': 'max', 
            'low': 'min', 
            'close': 'last', 
            'ticker': 'first', 
            'open_interest': 'sum', 
            'expiry_date': 'first'
        }

        fin_stock = (
            df_r.groupby(df_r.index.date, group_keys=False)   # per day
            .apply(lambda x: (
                x.resample(timedelta, label='left', closed='left', offset=time_offset)
                .agg(aggregation_dict)
            ))
        )
        fin_stock['date'] = fin_stock.index
        fin_stock['time'] = pd.to_datetime(fin_stock.date).dt.time.astype('str')
        fin_stock['date'] = pd.to_datetime(fin_stock.date).dt.date.astype('str')
        fin_stock.reset_index(inplace=True)
        fin_stock.drop('index', axis='columns', inplace=True)
        return fin_stock[['ticker','date','time','open','high','low','close','volume','open_interest','expiry_date']]

    def resample_stock_data_options(self, df:pd.DataFrame, timedelta:str = '15T', time_offset:str = '9h15min') -> pd.DataFrame:
        '''
        df: DataFrame dataframe with following formate [date	time	1	2	3	4	5	6	7	8	9	10]
        timedelta: str - '15T', '3T'.. sampling rate
        '''
        df_r = df.copy()

        # convert index to datetime
        df_r.index = pd.to_datetime(df_r.date+' '+df_r.time)
        df_r.drop('date', axis='columns', inplace=True)
        df_r.drop('time', axis='columns', inplace=True)

        # sort the index (evidently required by resample())
        df_r = df_r.sort_index()

        aggregation_dict = {
            1: 'first', 
            2: 'first', 
            3: 'first', 
            4: 'first', 
            5: 'max', 
            6: 'min', 
            7: 'last', 
            8: 'sum', 
            9: 'sum', 
            10: 'last', 
        }

        fin_stock = (
            df_r.groupby(df_r.index.date, group_keys=False)   # per day
            .apply(lambda x: (
                x.resample(timedelta, label='left', closed='left', offset=time_offset)
                .agg(aggregation_dict)
            ))
        )
        fin_stock['date'] = fin_stock.index
        fin_stock['time'] = pd.to_datetime(fin_stock.date).dt.time.astype('str')
        fin_stock['date'] = pd.to_datetime(fin_stock.date).dt.date.astype('str')
        fin_stock.reset_index(inplace=True)
        fin_stock.drop('index', axis='columns', inplace=True)
        return fin_stock[['date','time',1,2,3,4,5,6,7,8,9,10]]

    def analysis_cal(self, data:pd.DataFrame, column_name:str) -> pd.DataFrame:
        df = data.copy()
        df['gain'] = df[column_name].fillna(0)
        overall_gain = df.gain.sum()
        n_trade = df.shape[0]
        lose_trade = df[df.gain<0].shape[0]
        win_trade = df[df.gain>0].shape[0]
        if n_trade != 0:
            win_rate = win_trade/n_trade
            lose_rate = lose_trade/n_trade
        else:
            win_rate = 0
            lose_rate = 0
        avg_loss = df[df.gain<0].gain.mean()
        avg_gain = df[df.gain> 0].gain.mean()
        max_loss = df[df.gain<0].gain.min()
        max_gain = df[df.gain> 0].gain.max()
        xs = df.gain.cumsum()
        try:
            i = np.argmax(np.maximum.accumulate(xs) - xs) # end of the period
            j = np.argmax(xs[:i]) # start of period
            max_dd_amt = np.max(np.maximum.accumulate(xs) - xs)
            max_dd_trade = i-j
        except:
            max_dd_amt = 0
            max_dd_trade = 0

        overll_results = pd.DataFrame({'overall_gain':overall_gain,'n_trade':n_trade,'win_trade':win_trade,'lose_trade':lose_trade,
        'win_rate':win_rate,'lose_rate':lose_rate,'avg_gain':avg_gain,'avg_loss':avg_loss,
        'max_dd_amt':max_dd_amt,'max_dd_trade':max_dd_trade,'max_gain':max_gain,'max_loss':max_loss}, index=[0])
        return overll_results

    def analysis(self, data:pd.DataFrame, column_name:str) -> pd.DataFrame:
        df = data.copy()
        df['year'] = df.date
        df['month'] = df.date

        analyais_y = df.groupby([(pd.to_datetime(df.year).dt.year)]).apply(self.analysis_cal, (column_name))
        analyais_y.reset_index(inplace=True)
        analyais_y['month'] = 'all'
        analyais_y =  analyais_y[['year', 'month', 'overall_gain', 'n_trade', 'win_trade', 'lose_trade', 'win_rate', 'lose_rate', 'avg_gain', 'avg_loss', 'max_dd_amt', 'max_dd_trade', 'max_gain', 'max_loss']]

        analyais_m = df.groupby([(pd.to_datetime(df.year).dt.year), (pd.to_datetime(df.month).dt.month)]).apply(self.analysis_cal, (column_name))
        analyais_m.reset_index(inplace=True)
        analyais_m =  analyais_m[['year', 'month', 'overall_gain', 'n_trade', 'win_trade', 'lose_trade', 'win_rate', 'lose_rate', 'avg_gain', 'avg_loss', 'max_dd_amt', 'max_dd_trade', 'max_gain', 'max_loss']]

        analyais_all = self.analysis_cal(df, column_name)
        analyais_all['year'] = 'all'
        analyais_all['month'] = 'all'
        analyais_all = analyais_all[['year', 'month', 'overall_gain', 'n_trade', 'win_trade', 'lose_trade', 'win_rate', 'lose_rate', 'avg_gain', 'avg_loss', 'max_dd_amt', 'max_dd_trade', 'max_gain', 'max_loss']]

        combined = pd.concat([analyais_all, analyais_y, analyais_m]).reset_index(drop=True)
        combined['gain_max_dd'] = combined.overall_gain/combined.max_dd_amt
        combined.overall_gain = combined.overall_gain.astype(int)
        combined.max_dd_amt = combined.max_dd_amt.astype(int)
        return combined

    def create_new_column_on_cond(self, stc_ind_opt_data:pd.DataFrame, cond:str, column:str, default_val:Any, value:Any) -> pd.DataFrame:
        '''
        creating new columl based on condition
        stc_ind_opt_data: DataFrame
        cond: str condition code - '(stc_ind_opt_data.week == 0)', '(stc_ind_opt_data.week == 0) & (stc_ind_opt_data.date>='09:45:00')'
        column: str column name to be created
        value: value to be assigned to column at the given cond
        '''
        stc_ind_opt_data = stc_ind_opt_data.copy()
        if column not in stc_ind_opt_data.columns: stc_ind_opt_data[str(column)] = default_val
        to_excute = "stc_ind_opt_data.loc[" + cond + ", str(column)] = value"
        locals = {}
        exec(to_excute, {'stc_ind_opt_data':stc_ind_opt_data, 'column':column, 'value':value, 'pd':pd, 'np':np}, locals)
        return stc_ind_opt_data

    '''option_vals = {
        'create_new_column_on_cond': ['(stc_ind_opt_data.rsi >= 30) & (stc_ind_opt_data.rsi <= 70)', 'rsi_cond', 0, 1],
        'group_on_columns_ops': [['rsi_cond'], 'first'],
        'value_to_take_for_pnl': ['open_1', open_2]
    }'''
    def select_entry_exit_vals(self, data:pd.DataFrame, option_vals:dict) -> list:
        create_new_column_on_cond_ = option_vals['create_new_column_on_cond']
        group_on_columns_ops_ = option_vals['group_on_columns_ops']
        value_to_take_for_pnl = option_vals['value_to_take_for_pnl']
        data = data.copy()
        data = self.create_new_column_on_cond(data, create_new_column_on_cond_[0], create_new_column_on_cond_[1], create_new_column_on_cond_[2], create_new_column_on_cond_[3])
        data = self.group_on_columns_ops(data, group_on_columns_ops_[0], group_on_columns_ops_[1])
        try:
            return data[data[create_new_column_on_cond_[1]] == create_new_column_on_cond_[3]][value_to_take_for_pnl].iloc[0].to_list()
        except:
            _ret_ = []
            for i in value_to_take_for_pnl:
                _ret_.append('')
            return _ret_