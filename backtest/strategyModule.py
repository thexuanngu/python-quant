import pandas as pd
from interfaces import StrategyBase


class Strategy(StrategyBase):
    """Base for a single named strategy. Subclass this for each real
    strategy (e.g. SMACrossover) and implement generate_signals — don't
    instantiate Strategy directly."""

    def __init__(self, name: str):
        self.name = name

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        raise NotImplementedError  # implement in a subclass, e.g. SMACrossover(Strategy)
    
# Most basic strategy: Simple Moving Average
class SMA(Strategy):
    def __init__(self, window: int, threshold: float):
        super().__init__(f"SMA({window})")
        self.window = window  # The lookback period
        self.threshold = threshold  # The percentage of the SMA
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data.target
        sma   = price.copy().shift(1).rolling(self.window).mean()
        # TODO: In the future, I can specify WHAT trading signal it is (Buy/Sell) -> for now, true should suffice
        return price >= sma * (1 + self.threshold) | price <= sma * (1 - self.threshold) 
        
class SMACrossover(Strategy):
    def __init__(self, slowWindow: int, fastWindow: int):
            super().__init__(f"SMAC({slowWindow, fastWindow})")
            self.fastWindow = fastWindow  # The short period
            self.slowWindow = slowWindow  # The long period
            
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data["target"]

        fast = price.shift(1).rolling(self.fastWindow).mean()
        slow = price.shift(1).rolling(self.slowWindow).mean()

        return fast > slow
        # More 'complicated' signal
        # cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
        # cross_down = (fast < slow) & (fast.shift(1) >= slow.shift(1))
    
    


class StrategyModule:
    """Holds one or more strategies to run. Runs fine with a single
    strategy in the list — don't reach for multi-strategy blending until
    one strategy has run end-to-end."""

    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies