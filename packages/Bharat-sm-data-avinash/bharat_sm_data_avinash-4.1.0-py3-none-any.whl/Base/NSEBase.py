from datetime import datetime
from io import StringIO

import pandas as pd
import pydash as _
from .CustomRequest import CustomSession


class NSEBase(CustomSession):
    """
        A class to interact with the NSE (National Stock Exchange) API.

        Attributes:
            _base_url: base URL for the NSE API

        Methods:
            __init__(): Initializes the class and sets up the session and headers for all subsequent requests.
            get_market_status_and_current_val(index: str = 'NIFTY 50') -> tuple: Returns the market status and current value of a given index.
            get_last_traded_date() -> datetime.date: Returns the last traded date of NIFTY 50 index.
            get_second_wise_data(ticker_or_index: str = "NIFTY 50", is_index: bool = True, underlying_symbol: str = None) -> pd.DataFrame: Returns a dataframe with second wise data for a given index or stock.
            get_ohlc_data(ticker_or_idx: str = "NIFTY 50", timeframe: str = '5Min', is_index: bool = True, underlying_symbol: str = None) -> pd.DataFrame: Returns the OHLC data for a given ticker or index.
            search(search_text: str) -> dict: Searches for data related to an equity, derivative, or any type of asset traded on NSE.
            get_nse_turnover() -> pd.DataFrame: Provides the entire turnover happened in NSE exchange for the day or previous trading session as DataFrame.
            get_nse_equity_meta_info(ticker: str) -> dict: Returns the equity meta information for a given ticker.
            get_ohlc_from_charting(ticker: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame: Returns a DataFrame containing the OHLC data for a given ticker and timeframe from new Charting Website of NSE (https://charting.nseindia.com).  
            get_charting_mappings() -> pd.DataFrame: Returns a DataFrame containing the mappings for charting for all Equity and F&O instruments from the new Charting Website of NSE (https://charting.nseindia.com).
            search_charting_symbol(symbol: str, segment: str = "") -> dict: Searches for a symbol in the new NSE charting API with optional segment filter ("FO", "IDX", "EQ") and returns metadata including scripcode/token.
            get_charting_historical_data(symbol: str, token: str, symbol_type: str = "Index", chart_type: str = "D", time_interval: int = 1, from_date: int = 0, to_date: int = None) -> pd.DataFrame: Fetches historical OHLC data from the new NSE charting API using token. Supports symbol_type: "Index", "Equity", "Futures", "Options".
            get_ohlc_from_charting_v2(symbol: str, timeframe: str = "1Day", start_date: datetime = None, end_date: datetime = None, symbol_type: str = "Index", segment: str = "") -> pd.DataFrame: Simplified wrapper to fetch historical data from new NSE charting API with optional segment filter. Supports symbol_type: "Index", "Equity", "Futures", "Options".
    """

    def __init__(self):
        """
            The __init__ function is called when the class is instantiated.
            It sets up the session and headers for all subsequent requests.
    
            :param self: Represent the instance of the class

            :return: Nothing
        """

        super().__init__(headers={
            'authority': 'www.nseindia.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://www.nseindia.com/',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54',
        })
        
        self._base_url = 'https://www.nseindia.com'
        self._charting_base_url = 'https://charting.nseindia.com'
        self._charting_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://charting.nseindia.com/',
            'Content-Type': 'application/json',
            'Origin': 'https://charting.nseindia.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.hit_and_get_data(self._base_url)
        self.hit_and_get_data(f'{self._charting_base_url}')
        # This will call the main website and sets cookies into a session object if available

    # ----------------------------------------------------------------------------------------------------------------
    # Utility Functions

    def get_market_status_and_current_val(self, index: str = 'NIFTY 50') -> tuple:
        """
            The get_market_status_and_current_val function returns the market status and current value of a given index.

            :param self: Represent the instance of the class
            :param index: Get the market status and last price of a particular index

            :return: A tuple of the market status and the current value
        """

        response = self.hit_and_get_data(f'{self._base_url}/api/marketStatus').get('marketState')
        status = _.get(_.find(response, {'index': 'NIFTY 50'}), 'marketStatus', 'Close')
        last_price = _.get(_.find(response, {'index': index}), 'last')
        return status, last_price

    def get_last_traded_date(self):
        """
            The get_last_traded_date function returns the last traded date of NIFTY 50 index.

            :param self: Represent the instance of the class
            :return: The date of the last traded day
        """
        response = self.hit_and_get_data(f'{self._base_url}/api/marketStatus').get('marketState')
        last_traded = _.get(_.find(response, {'index': 'NIFTY 50'}), 'tradeDate')
        return datetime.strptime(last_traded, '%d-%b-%Y %H:%M').date()

    # ----------------------------------------------------------------------------------------------------------------
    # Common Functions - works for both Equity as well index-related data fetches

    def get_second_wise_data(self, ticker_or_index: str = "NIFTY 50", is_index: bool = True, underlying_symbol: str = None) -> pd.DataFrame:
        """
            The get_second_wise_data function returns a dataframe with the following columns:
                timestamp - The time at which the price was recorded.
                price - The value of the index/stock at that particular time.

            :param self: Bind the method to a class
            :param ticker_or_index: Specify the index for which we want to get data
            :param is_index: (optional) Determine whether the index is an index or not
            :param underlying_symbol: (optional) This is required for fetching derivatives OHLC data where underlying
            assets ticker

            :return: A dataframe with second wise data
        """
         # set the cookies
        self.hit_and_get_data(f'{self._base_url}/get-quotes/equity', params={'symbol': ticker_or_index})

        if not ticker_or_index.endswith('EQN') and not is_index:
            ticker_or_index += 'EQN'

        params = {'index': ticker_or_index}
        if is_index:
            params['indices'] = True

        if underlying_symbol is not None:
            params['underlyingsymbol'] = underlying_symbol
        response = self.hit_and_get_data(f'{self._base_url}/api/chart-databyindex', params=params)
        params['preopen'] = True
        pre_response = self.hit_and_get_data(f'{self._base_url}/api/chart-databyindex', params=params)
        datapoint_size = 2
        try:
            datapoint_size = len(response.get('grapthData', [])[0])
        except:
            pass
        df = pd.DataFrame(_.get(pre_response, 'grapthData', []) + _.get(response, 'grapthData', []),
                          columns=['timestamp', 'price'] if datapoint_size == 2 else ['timestamp', 'price', 'market_time'])
        df['timestamp'] = df['timestamp'] / 1000
        df['timestamp'] = df['timestamp'].apply(datetime.fromtimestamp)
        df['timestamp'] = df['timestamp'] - pd.Timedelta(hours=5, minutes=30)
        return df

    def get_ohlc_data(self, ticker_or_idx: str = "NIFTY 50", timeframe: str = '5Min', is_index: bool = True,
                      underlying_symbol: str = None) -> pd.DataFrame:
        """
            The get_ohlc_data function takes in a ticker or index name, and returns the OHLC data for that ticker/index.
            The function also takes in a timeframe parameter which can be used to specify the time interval of each
            candle. By default, it is set to 5 minutes.

            :param underlying_symbol: Index Symbol for options strikes
            :param self: Represents the instance of the class
            :param ticker_or_idx: Specify the ticker or index for which we want to get data
            :param timeframe: (optional) Define the time interval for which we want to get the data
            :param is_index: (optional) Determine whether the ticker is an index or a stock

            :return: The ohlc data for a given ticker or index
        """

        df = self.get_second_wise_data(ticker_or_idx, is_index, underlying_symbol)
        df.set_index(['timestamp'], inplace=True)
        df = df['price'].resample(timeframe).ohlc()
        return df

    # ----------------------------------------------------------------------------------------------------------------
    # Search and exchange related data

    def search(self, search_text: str) -> dict:
        """
            The search function can be used to take out data related to an Equity/ Derivatives or any type of asset
            traded on NSE, this is required to take out symbol/ticker ids respective to that asset

            :param self: Represent the instance of the class
            :param search_text: Specify the ticker or index for which we want to get data

            :return: The ohlc data for a given ticker or index
        """

        params = {
            'q': search_text,
        }

        response = self.hit_and_get_data(f'{self._base_url}/api/search/autocomplete', params=params)
        return response

    def get_nse_turnover(self) -> pd.DataFrame:
        """
            The `get_nse_turnover` provides the entire turnover happened in NSE exchange for the day / previous trading
            session as DataFrame.

           :param self: Represent the instance of the class

           :return: The exchange turnover data in the DataFrame format
       """

        response = self.hit_and_get_data(f'{self._base_url}/api/NextApi/apiClient', params={'functionName':'getMarketTurnoverSummary'})
        data = []
        for key in response.get('data', {}):
            try:
                data = data + response.get('data', {}).get(key, [])
            except:
                pass
        df = pd.DataFrame(data)
        return df

    def get_nse_equity_meta_info(self, ticker: str) -> dict:
        params = {
            'symbol': ticker,
        }
        # set the cookies
        self.hit_and_get_data(f'{self._base_url}/get-quotes/equity', params=params)

        response = self.hit_and_get_data(f'{self._base_url}/api/equity-meta-info', params=params)
        return response

    def get_ohlc_from_charting(self, ticker: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
            The get_ohlc_from_charting function returns a DataFrame containing the OHLC data for a given ticker and
            timeframe.

            :param self: Represent the instance of the class
            :param ticker: Specify the ticker for which we want to get the data (!! Its not same as NSE website ticker, Get the mapping from `get_charting_mappings()` function !!)
            :param timeframe: Specify the time interval for which we want to get the data
            :param start_date: Specify the start date of the data
            :param end_date: Specify the end date of the data
            :return: A DataFrame containing OHLC data for a given ticker and timeframe
        """

        time_mappings = {
            '1Min': ('I', 1),
            '5Min': ('I', 5),
            '15Min': ('I', 15),
            '30Min': ('I', 30),
            '60Min': ('I', 60),
            '1Day': ('D', 1),
            '1Week': ('W', 1),
            '1Month': ('M', 1),
        }
        if timeframe not in time_mappings:
            raise ValueError(f"Unsupported timeframe: {timeframe}; supported timeframes are {list(time_mappings.keys())}")
        params = {
            'tradingSymbol': ticker,
            'exch': 'N',
            'chartStart': 0,
            'chartPeriod': time_mappings[timeframe][0],
            'timeInterval': time_mappings[timeframe][1],
            'fromDate':int(start_date.timestamp()),
            'toDate': int(end_date.timestamp())
        }

        
        # Set the cookies
        self.hit_and_get_data(f'{self._charting_base_url}', params={'symbol': ticker})



        response = self.hit_and_get_data(f'{self._charting_base_url}//Charts/ChartData', params=params)
        df = pd.DataFrame({
            'timestamp': response.get('t', []),
            'open': response.get('o', []),
            'high': response.get('h', []),
            'low': response.get('l', []),
            'close': response.get('c', []),
            'volume': response.get('v', [])
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df

    def get_charting_mappings(self) -> pd.DataFrame:
        """
            The get_charting_mappings function returns a dictionary containing the mappings for charting.

            :param self: Represent the instance of the class

            :return: A DataFrame containing the mappings for charting for all Equity and F&O instruments
        """
        
        url_endpoints = ['/Charts/GetEQMasters', '/Charts/GetFOMasters']
        df = pd.DataFrame()
        for endpoint in url_endpoints:
            df = pd.concat([df, pd.read_csv(StringIO(self.session.get(f'{self._charting_base_url}{endpoint}', headers=self.headers).text), sep='|')], ignore_index=True)
        return df

    def search_charting_symbol(self, symbol: str, segment: str = "") -> dict:
        """
            The search_charting_symbol function searches for a symbol in the new NSE charting API
            and returns the symbol metadata including scripcode/token needed for historical data.

            :param self: Represent the instance of the class
            :param symbol: Symbol name to search (e.g., "NIFTY 50", "RELIANCE")
            :param segment: (optional) Market segment filter - "" (all), "FO" (Futures & Options), "IDX" (Index), "EQ" (Equity)

            :return: Dict containing symbol information with scripcode, instrumentType, exchange, etc.
            
            Examples:
                # Search all segments
                nse.search_charting_symbol("NIFTY")
                
                # Search only indices
                nse.search_charting_symbol("NIFTY", segment="IDX")
                
                # Search only equities
                nse.search_charting_symbol("RELIANCE", segment="EQ")
                
                # Search futures & options
                nse.search_charting_symbol("NIFTY", segment="FO")
        """
        
        # Validate segment parameter
        valid_segments = ["", "FO", "IDX", "EQ"]
        if segment not in valid_segments:
            raise ValueError(f"Invalid segment '{segment}'. Valid values are: {valid_segments}")
        
        payload = {
            "symbol": symbol,
            "segment": segment
        }
        
        response = self.post_and_get_data(
            f'{self._charting_base_url}/v1/exchanges/symbolsDynamic',
            json_data=payload,
            headers=self._charting_headers
        )
        
        return response

    def get_charting_historical_data(self, symbol: str, token: str, symbol_type: str = "Index", 
                                     chart_type: str = "D", time_interval: int = 1,
                                     from_date: int = 0, to_date: int = None) -> pd.DataFrame:
        """
            The get_charting_historical_data function fetches historical OHLC data from the new NSE charting API.

            :param self: Represent the instance of the class
            :param symbol: Symbol name (e.g., "NIFTY 50", "RELIANCE")
            :param token: Scripcode/token obtained from search_charting_symbol (e.g., "26000" for NIFTY 50)
            :param symbol_type: (optional) Type of symbol - "Index", "Equity", "Futures", or "Options" (default: "Index")
            :param chart_type: (optional) Chart type - "D" (Daily), "I" (Intraday), "W" (Weekly), "M" (Monthly) (default: "D")
            :param time_interval: (optional) Time interval in minutes for intraday or 1 for daily/weekly/monthly (default: 1)
            :param from_date: (optional) Start date as Unix timestamp (default: 0 for all available data)
            :param to_date: (optional) End date as Unix timestamp (default: current time)

            :return: DataFrame containing OHLC data with columns: time, open, high, low, close, volume
        """
        
        # Validate symbol_type
        valid_symbol_types = ["Index", "Equity", "Futures", "Options"]
        if symbol_type not in valid_symbol_types:
            raise ValueError(f"Invalid symbol_type '{symbol_type}'. Valid values are: {valid_symbol_types}")
        
        if to_date is None:
            to_date = int(datetime.now().timestamp())
        
        payload = {
            "token": str(token),
            "fromDate": from_date,
            "toDate": to_date,
            "symbol": symbol,
            "symbolType": symbol_type,
            "chartType": chart_type,
            "timeInterval": time_interval
        }
        
        response = self.post_and_get_data(
            f'{self._charting_base_url}/v1/charts/symbolHistoricalData',
            json_data=payload,
            headers=self._charting_headers
        )
        
        if response.get('status') and response.get('data'):
            df = pd.DataFrame(response['data'])
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'], unit='ms')
                df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            return df
        else:
            return pd.DataFrame()

    def get_ohlc_from_charting_v2(self, symbol: str, timeframe: str = "1Day", 
                                   start_date: datetime = None, end_date: datetime = None,
                                   symbol_type: str = "Index", segment: str = "") -> pd.DataFrame:
        """
            The get_ohlc_from_charting_v2 function is a simplified wrapper that fetches historical data
            from the new NSE charting API. It automatically searches for the symbol and fetches data.

            :param self: Represent the instance of the class
            :param symbol: Symbol name (e.g., "NIFTY 50", "RELIANCE")
            :param timeframe: (optional) Timeframe - "1Min", "5Min", "15Min", "30Min", "60Min", "1Day", "1Week", "1Month" (default: "1Day")
            :param start_date: (optional) Start date as datetime object (default: beginning of available data)
            :param end_date: (optional) End date as datetime object (default: current time)
            :param symbol_type: (optional) Type of symbol - "Index", "Equity", "Futures", or "Options" (default: "Index")
            :param segment: (optional) Market segment filter - "" (all), "FO" (Futures & Options), "IDX" (Index), "EQ" (Equity) (default: "")

            :return: DataFrame containing OHLC data with columns: time, open, high, low, close, volume
            
            Examples:
                # Get daily data for NIFTY 50 (Index)
                nse.get_ohlc_from_charting_v2("NIFTY 50", "1Day", symbol_type="Index", segment="IDX")
                
                # Get equity data with segment filter
                nse.get_ohlc_from_charting_v2("RELIANCE", "1Day", symbol_type="Equity", segment="EQ")
                
                # Get futures data
                nse.get_ohlc_from_charting_v2("NIFTY 25JAN2024 FUT", "1Day", symbol_type="Futures", segment="FO")
                
                # Get options data
                nse.get_ohlc_from_charting_v2("NIFTY 25JAN2024 23500 CE", "1Day", symbol_type="Options", segment="FO")
        """
        
        # Validate symbol_type
        valid_symbol_types = ["Index", "Equity", "Futures", "Options"]
        if symbol_type not in valid_symbol_types:
            raise ValueError(f"Invalid symbol_type '{symbol_type}'. Valid values are: {valid_symbol_types}")
        
        time_mappings = {
            '1Min': ('I', 1),
            '5Min': ('I', 5),
            '15Min': ('I', 15),
            '30Min': ('I', 30),
            '60Min': ('I', 60),
            '1Day': ('D', 1),
            '1Week': ('W', 1),
            '1Month': ('M', 1),
        }
        
        if timeframe not in time_mappings:
            raise ValueError(f"Unsupported timeframe: {timeframe}; supported timeframes are {list(time_mappings.keys())}")
        
        chart_type, time_interval = time_mappings[timeframe]
        
        # Search for symbol to get token (with segment filter)
        search_result = self.search_charting_symbol(symbol, segment=segment)
        
        if not search_result.get('status') or not search_result.get('data'):
            raise ValueError(f"Symbol '{symbol}' not found in charting API" + (f" for segment '{segment}'" if segment else ""))
        
        # Get the first matching symbol's token
        symbol_data = search_result['data'][0]
        token = symbol_data['scripcode']
        
        # Convert dates to timestamps
        from_timestamp = 0 if start_date is None else int(start_date.timestamp())
        to_timestamp = int(datetime.now().timestamp()) if end_date is None else int(end_date.timestamp())
        
        # Fetch historical data
        df = self.get_charting_historical_data(
            symbol=symbol,
            token=token,
            symbol_type=symbol_type,
            chart_type=chart_type,
            time_interval=time_interval,
            from_date=from_timestamp,
            to_date=to_timestamp
        )
        
        return df