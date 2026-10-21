import pandas as pd
import yfinance as yf
from interfaces import DataSourceBase


class DataSource(DataSourceBase):
    def __init__(self, source: str, nature: str, yfTickers: list[str]):
        self.source = source  # e.g. "yfinance", "'static.csv'", "live"
        self.nature = nature  # e.g. "historical", "live"
        self.yfTickers = yfTickers  # e.g. for the yfinance 'download' method

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # This can be the 'super' process (after specific datasource preprocess)
        # TODO: point-in-time alignment, forward-fill guards, corporate
        # action adjustments — this is where look-ahead bias gets caught
        # or silently let through. Don't skip this once real data is wired in.
        
        # Basic preprocessing for now
        if self.source == "yfinance":
            data.rename(columns={'close':'target'}, inplace=True)
            return data
        raise ValueError("Currently unsupported data source")


class DataModule:
    def __init__(self, dataSource: DataSource):
        self.dataSource = dataSource

    def load(self, start_date, end_date, freq: str) -> pd.DataFrame:
        ds = self.dataSource
        if ds.source != "yfinance":
            raise NotImplementedError(f"Unsupported source: {ds.source}")
        if len(ds.yfTickers) != 1:
            raise NotImplementedError("MVP is single-ticker; rolling ops need groupby for multi.")

        raw = yf.download(tickers=ds.yfTickers, start=start_date, end=end_date,
                          interval=freq.lower(), auto_adjust=True, progress=False)
        if raw.empty:
            raise ValueError(f"No data returned for {ds.yfTickers} {start_date}->{end_date}")
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)  # drop the ticker level
        raw.columns = [c.lower().replace(" ", "_") for c in raw.columns]
        return ds.preprocess_data(raw)
        
        
            