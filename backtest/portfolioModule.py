import numpy as np
from backtestConfig import BacktestConfig
from interfaces import PortfolioBase


class Portfolio(PortfolioBase):
    """Stateful ledger, mutated once per bar inside the event loop.
    Preallocate arrays"""

    def __init__(self, config: BacktestConfig, n_bars: int):
        self.config = config
        self.n_bars_ = n_bars  # length of THIS run, derived from loaded data
        self.cash = config.initial_capital
        self.position = 0.0
        self._equity = np.full(n_bars, np.nan, dtype=np.float64)
        self.recent_price = np.nan
        self._t = 0

    # Apply computations from ExecutionModule and position sizing from engine
    def apply_fill(self, fill_price: float, fill_qty: float, cost: float = 0.0) -> None:
        self.cash -= fill_price * fill_qty + cost # cost = transaction cost
        self.position += fill_qty

    # value portfolio at this price TODO: Expand to support multi-asset
    def mark_to_market(self, price: float) -> float:
        equity = self.equity(price)
        self._equity[self._t] = equity
        self._t += 1
        self.recent_price = price
        return equity
    
    # current value of portfolio
    def equity(self, price: float) -> float:
        return self.cash + self.position * price  # cash + stock

    # annotation makes the method behave like ... a property
    @property
    def equity_curve(self) -> np.ndarray:
        return self._equity[: self._t]

    # leverage: gross exposure / equity TODO: find a way to use it
    @property
    def leverage(self) -> float:
        # TODO: Define behaviour when equity <= 0
        # exposure vs equity — cheap running risk check, no need to wait for resultsModule
        return abs(self.position * self.recent_price) / self._equity[self._t - 1] if self._t else 0.0