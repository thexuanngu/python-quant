# portfolioModule.py
from dataclasses import dataclass
import numpy as np
from backtestConfig import BacktestConfig

class Portfolio:
    def __init__(self, config: BacktestConfig, n_bars: int):
        ...