from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return target positions/signals indexed like `data`. No lookahead."""

class ExecutionModel(ABC):
    @abstractmethod
    def fill(self, order_size: float, price: float, adv: float) -> tuple[float, float]:
        """Return (fill_price, realized_cost) given order size and avg daily volume."""

class Portfolio(ABC):
    @abstractmethod
    def update(self, fill_price: float, fill_qty: float, timestamp) -> None: ...
    @abstractmethod
    def mark_to_market(self, price: float) -> float: ...

class DataSource(ABC):
    @abstractmethod
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame: ...