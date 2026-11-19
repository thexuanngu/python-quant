import pandas as pd
import numpy as np
from interfaces import StrategyBase

# --- Strategy Orchestration --- #

class Strategy(StrategyBase):
    """Base for a single named strategy. Subclass this for each real
    strategy (e.g. SMACrossover) and implement generate_signals — 
    don't instantiate Strategy directly."""

    def __init__(self, name: str):
        self.name = name

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        raise NotImplementedError  # implement in a subclass
   
class SingleWindowStrategy(Strategy):
    """Base for a single windowed named strategy. Subclass this 
    for each real strategy that uses .rolling (e.g. SMACrossover) 
    to generate_signals."""
    def __init__(self, name: str, window: int, threshold: float = 0.0):
        if threshold <= 0: raise ValueError("threshold must be non-negative")
        if window <= 0: raise ValueError("window must be positive")
        super().__init__(name)
        self.window = window  # The lookback period
        self.threshold = threshold  # The percentage of the _MA
    
    
class StrategyModule:
    """Holds one or more strategies to run. Runs fine with a single
    strategy in the list — don't reach for multi-strategy blending until
    one strategy has run end-to-end."""

    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies   
    
# --- Specific Strategies --- #

# Simple Moving Average
class SMA(SingleWindowStrategy):
    def __init__(self, window: int, threshold: float):
        super().__init__(f"SMA({window})",  window, threshold)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data['target']
        sma   = price.copy().shift(1).rolling(self.window).mean()
        nan   = pd.Series(np.nan, index=price.index)
        
        long_leg = nan.copy()
        # px has dipped below the sma
        long_leg[price <= sma * (1 - self.threshold)] = 1 # enter long
        long_leg[price >= sma]                        = 0 # exit long (realize pnl)
        
        short_leg = nan.copy()
        # px has dipped above the sma
        short_leg[price >= sma * (1 + self.threshold)] = 1  # enter short 
        short_leg[price <= sma]                        = 0  # exit short (realize pnl)
        
        return (long_leg.ffill().fillna(0) - short_leg.ffill().fillna(0)).astype(int)
        
# Exponential Moving Average
class EMA(SingleWindowStrategy):
    def __init__(self, window: int, threshold: float = 0.0, adjust: bool = False):
        super().__init__(f"EMA({window})", window, threshold)
        self.adjust = adjust
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data['target']
        ema   = price.copy().shift(1).ewm(span=self.window, # TODO: Do I need a copy?
                                          adjust=self.adjust).mean()
        nan   = pd.Series(np.nan, index=price.index)
        
        long_leg = nan.copy()
        long_leg[price <= ema * (1 - self.threshold)] = 1 # enter long
        long_leg[price >= ema]                        = 0 # exit long (realize pnl)
        
        short_leg = nan.copy()
        short_leg[price >= ema * (1 + self.threshold)] = 1  # enter short 
        short_leg[price <= ema]                        = 0  # exit short (realize pnl)
        
        return (long_leg.ffill().fillna(0) - short_leg.ffill().fillna(0)).astype(int)

class TrendPullback(Strategy):
    def __init__(self, slowWindow: int, fastWindow: int, threshold: float):
            if fastWindow >= slowWindow: raise ValueError("fastWindow must be less than slowWindow")
            if threshold <= 0: raise ValueError("threshold must be positive")
            
            super().__init__(f"TrendPullback{slowWindow, fastWindow}")
            self.fastWindow = fastWindow  # The short period
            self.slowWindow = slowWindow  # The long period
            self.threshold  = threshold   # The percentage of the SMA

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        price = data['target']

        fast = price.shift(1).rolling(self.fastWindow).mean()
        slow = price.shift(1).rolling(self.slowWindow).mean()
        nan = pd.Series(np.nan, index=price.index)
        
        long_leg = nan.copy()
        # momentum is positive, but price has dipped below
        long_leg[(fast > slow) & (price <= fast * (1 - self.threshold))] = 1  # enter long position
        long_leg[price >= fast                                         ] = 0  # exit long position
        
        short_leg = nan.copy()
        # momentum is negative, but price has gone above buy threshold
        short_leg[(fast < slow) & (price >= fast * (1 + self.threshold))] = 1  # enter short position
        short_leg[price <= fast                                         ] = 0  # exit short position

        return (long_leg.ffill().fillna(0) - short_leg.ffill().fillna(0)).astype(int)

