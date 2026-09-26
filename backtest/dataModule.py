import pandas as pd
import yfinance as yf
from backtest.interfaces import DataSourceBase


class DataSource(DataSourceBase):
    def __init__(self, source: str, nature: str, yfTickers: list[str]):
        self.source = source  # e.g. "yfinance", "static_csv", "live"
        self.nature = nature  # e.g. "historical", "live"
        self.yfTickers = yfTickers  # e.g. for the yfinance 'download' method

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # This can be the 'super' process (after specific datasource preprocess)
        # TODO: point-in-time alignment, forward-fill guards, corporate
        # action adjustments — this is where look-ahead bias gets caught
        # or silently let through. Don't skip this once real data is wired in.
        
        # Basic preprocessing for now
        return data
        
        raise NotImplementedError


class DataModule:
    def __init__(self, dataSource: DataSource):
        self.dataSource = dataSource

    def load(self, start_date, end_date, freq: str) -> pd.DataFrame:
        # TODO: fetch raw data from self.dataSource, then run it through
        # self.dataSource.preprocess_data(raw) before returning.
        try: 
            if (self.dataSource.source == "yfinance"):  # just a call to the download
                print("Fetching yfinance price data")  # NOTE: yfinance doesn't support intraday data beyond the last 60 days
                raw = yf.download(tickers=self.dataSource.yfTickers, 
                                start=start_date, 
                                end=end_date,
                                interval=freq)
                if (len(self.dataSource.yfTickers) > 1):
                    raw = raw.stack(future_stack=True)  # Stack multi-level columns ('Adj Close', 'Close', etc.) into rows
                    raw.index.names = ['date', 'ticker']  # optional index renaming here
                raw.columns = [col.lower().replace(' ', '_') for col in raw.columns]
                
                # the user can choose to save the data here if they would like -> won't implement for now
                return self.dataSource.preprocess_data(raw)
            else:  # handle other data cases later
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching price data from yfinance: {e}")
            return pd.DataFrame()
        
        
            