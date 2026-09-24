from abc import ABC, abstractmethod
import pandas as pd


class StrategyBase(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return target positions/signals indexed like `data`."""


class ExecutionModelBase(ABC):
    @abstractmethod
    def fill(self, order_size: float, price: float, adv: float) -> tuple[float, float]:
        """Return (fill_price, realized_cost) given order size and avg daily volume."""


class PortfolioBase(ABC):
    @abstractmethod
    def apply_fill(self, fill_price: float, fill_qty: float) -> None: ...

    @abstractmethod
    def mark_to_market(self, price: float) -> float: ...


class DataSourceBase(ABC):
    @abstractmethod
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame: ...