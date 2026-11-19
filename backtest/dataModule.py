import pandas as pd
import yfinance as yf
from interfaces import DataSourceBase

# TODO: In the future, check for NaN, missing prices, negative prices

class DataSource(DataSourceBase):  # Responsible for source-specific preprocessing
    def __init__(self, source: str, nature: str, yfTickers: list[str]):
        self.source = source  # e.g. "yfinance", "'_.csv'", "___-api", "_.parquet"
        self.nature = nature  # e.g. "historical", "live"
        # TODO: extract the yfinance data into its own subclass
        self.yfTickers = yfTickers  # e.g. for the yfinance 'download' method

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # This can be the 'super' process (after specific datasource preprocess)
        # TODO: point-in-time alignment, forward-fill guards, corporate
        # action adjustments — this is where look-ahead bias gets caught
        # or silently let through. Don't skip this once real data is wired in.
        
        # TODO: This can be tailored for different sources
        if self.source == "yfinance":
            # TODO: Eventually support multiple tickers
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)  # drop the ticker level
            
            # Ensure consistent labelling
            data.columns = [c.lower().replace(" ", "_") for c in data.columns]
            data.rename(columns={'close':'target'}, inplace=True)
            return data
        raise ValueError("Currently unsupported data source")

# TODO: In the future, DataModule should be able to support multiple DataSources (to get us more signals)
class DataModule:  # Retrieves data
    def __init__(self, dataSource: DataSource):
        self.dataSource = dataSource

    # TODO: Eventually expand into multiple data sources (for more alpha)
    def load(self, start_date, end_date, freq: str) -> pd.DataFrame:
        ds = self.dataSource  #TODO: Eventually expand the logic to support multiple data sources
        
        match ds.source.lower():
            case "yfinance":
                if len(ds.yfTickers) != 1:  # TODO: Eventually expand this to support multi-level
                    raise NotImplementedError("MVP is single-ticker; rolling ops need groupby for multi.")
                
                # load yfinance data TODO: Eventually move this into the 'yfinance' DataProvider
                raw = yf.download(tickers=ds.yfTickers, 
                                  start=start_date, end=end_date, interval=freq.lower(), 
                                  auto_adjust=True, progress=False)  # TODO: Confirm if auto_adjust=True is what we want
                
                # safely try to load the yfinance data
                if raw is None or raw.empty:
                    raise ValueError(f"No valid data returned for {ds.yfTickers} {start_date}->{end_date}")
                
                preprocessed = ds.preprocess_data(raw)
            case _:
                raise NotImplementedError(f"Unsupported source: {ds.source}")

        # last safety checks before data can be used
        if "target" not in preprocessed.columns:
            raise ValueError("Processed data must contain a 'target' column")
        
        if "volume" not in preprocessed.columns:  # TODO: This field is relevant for price impact
            raise ValueError("Processed data must contain a 'volume' column")

        return preprocessed
        
    
# Placeholder for 'grids' of values
#TODO: CachedData and DataModule could implement a shared DataProvider in the future
class CachedData:  # Provide the same data for repeated backtests
    def __init__(self, df): self.df = df
    def load(self, *_): return self.df
        
        
            