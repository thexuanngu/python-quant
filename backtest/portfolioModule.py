import numpy as np
from backtestConfig import BacktestConfig
from interfaces import PortfolioBase


class Portfolio(PortfolioBase):
    """Stateful ledger, mutated once per bar inside the event loop.
    Preallocate arrays"""

    def __init__(self, config: BacktestConfig, n_bars: int):
        self.config = config
        self.n_bars_ = n_bars          # length of THIS run, derived from loaded data
        self.cash = config.initial_capital
        self.position = 0.0
        self._equity = np.empty(n_bars, dtype=np.float64)
        self._equity[:] = np.nan
        self._t = 0

    def apply_fill(self, fill_price: float, fill_qty: float) -> None:
        self.cash -= fill_price * fill_qty
        self.position += fill_qty

    def mark_to_market(self, price: float) -> float:
        equity = self.cash + self.position * price
        self._equity[self._t] = equity
        self._t += 1
        return equity

    @property
    def equity_curve(self) -> np.ndarray:
        return self._equity[: self._t]

    @property
    def leverage(self) -> float:
        # exposure vs equity — cheap running risk check, no need to wait for resultsModule
        return abs(self.position) / self._equity[self._t - 1] if self._t else 0.0