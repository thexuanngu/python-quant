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


class StrategyModule:
    """Holds one or more strategies to run. Runs fine with a single
    strategy in the list — don't reach for multi-strategy blending until
    one strategy has run end-to-end."""

    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies