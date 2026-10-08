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
        signals = pd.Series(0, index=price.index)
        signals[price >= sma * (1 + self.threshold)] = -1  # sell
        signals[price <= sma * (1 - self.threshold)] = 1   # buy

        return signals
        
class SMACrossover(Strategy):
    def __init__(self, slowWindow: int, fastWindow: int, threshold: float):
            super().__init__(f"SMAC({slowWindow, fastWindow})")
            self.fastWindow = fastWindow  # The short period
            self.slowWindow = slowWindow  # The long period
            self.threshold = threshold  # The percentage of the SMA

            
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data.target

        fast = price.shift(1).rolling(self.fastWindow).mean()
        slow = price.shift(1).rolling(self.slowWindow).mean()

        signals = pd.Series(0, index=price.index)
        signals[(fast > slow) & (price <= fast * (1 - self.threshold)) ] = 1  # momentum is positive, but price has dipped below
        signals[(fast < slow) & (price >= fast * (1 + self.threshold)) ] = -1  # momentum is negative, but price has gone above buy threshold

        return signals
    
class StrategyModule:
    """Holds one or more strategies to run. Runs fine with a single
    strategy in the list — don't reach for multi-strategy blending until
    one strategy has run end-to-end."""

    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies