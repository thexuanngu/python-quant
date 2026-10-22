import pandas as pd
import numpy as np
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
        if threshold <= 0: raise ValueError("threshold cannot be negative")
        
        super().__init__(f"SMA({window})")
        self.window = window  # The lookback period
        self.threshold = threshold  # The percentage of the SMA
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data['target']
        sma   = price.copy().shift(1).rolling(self.window).mean()
        nan   = pd.Series(np.nan, index=price.index)
        
        long_leg = nan.copy()
        long_leg[price <= sma * (1 - self.threshold)] = 1 # enter long
        long_leg[price >= sma]                        = 0 # exit long (realize pnl)
        
        short_leg = nan.copy()
        short_leg[price >= sma * (1 + self.threshold)] = 1  # enter short 
        short_leg[price <= sma]                        = 0  # exit long (realize pnl)
        
        return (long_leg.ffill().fillna(0) - short_leg.ffill().fillna(0)).astype(int)
        
class TrendPullback(Strategy):
    def __init__(self, slowWindow: int, fastWindow: int, threshold: float):
            if fastWindow >= slowWindow: raise ValueError("fastWindow must be less than slowWindow")
            if threshold <= 0: raise ValueError("threshold cannot be negative")
            
            super().__init__(f"SMAC{slowWindow, fastWindow}")
            self.fastWindow = fastWindow  # The short period
            self.slowWindow = slowWindow  # The long period
            self.threshold  = threshold  # The percentage of the SMA

            
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data['target']

        fast = price.shift(1).rolling(self.fastWindow).mean()
        slow = price.shift(1).rolling(self.slowWindow).mean()
        nan = pd.Series(np.nan, index=price.index)
        
        long_leg = nan.copy()
        # momentum is positive, but price has dipped below
        long_leg[(fast > slow) & (price <= fast * (1 - self.threshold)) ] = 1  # enter long position
        long_leg[(fast > slow) & (price >= fast)                        ] = 0  # exit long position
        
        short_leg = nan.copy()
        # momentum is negative, but price has gone above buy threshold
        short_leg[(fast < slow) & (price >= fast * (1 + self.threshold)) ] = 1  # enter short position
        short_leg[(fast < slow) & (price <= fast)                        ] = 0  # exit long position

        return (long_leg.ffill().fillna(0) - short_leg.ffill().fillna(0)).astype(int)

# --- Strategy Orchestrator --- #

class StrategyModule:
    """Holds one or more strategies to run. Runs fine with a single
    strategy in the list — don't reach for multi-strategy blending until
    one strategy has run end-to-end."""

    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies