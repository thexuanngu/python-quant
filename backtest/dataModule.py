import pandas as pd
from interfaces import DataSourceBase


class DataSource(DataSourceBase):
    def __init__(self, source: str, nature: str):
        self.source = source  # e.g. "yfinance", "static_csv", "live"
        self.nature = nature  # e.g. "historical", "live"

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # TODO: point-in-time alignment, forward-fill guards, corporate
        # action adjustments — this is where look-ahead bias gets caught
        # or silently let through. Don't skip this once real data is wired in.
        raise NotImplementedError
    
class CSVDataSource(DataSource):
    def __init__(self, filepath: str):
        self.filepath = filepath  # CSV data (for now) would be locally loaded
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # TODO: Implement
        return data


class DataModule:
    def __init__(self, dataSource: DataSource):
        self.dataSource = dataSource

    def load(self, start_date, end_date, freq: str) -> pd.DataFrame:
        # TODO: fetch raw data from self.dataSource, then run it through
        # self.dataSource.preprocess_data(raw) before returning.
        raw = self.datasource.data
        
        raise NotImplementedError