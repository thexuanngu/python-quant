from backtestConfig import BacktestConfig
from portfolioModule import Portfolio
from dataModule import DataModule
import resultsModule
import backtest.executionModule as executionModule
import strategyModule
import vizModule
import numpy as np

class BacktestEngine:
    def __init__(self, config: BacktestConfig, dataModule, strategyModule,
                 executionModule, resultsModule, vizModule):
        self.config = config
        self.portfolio = Portfolio(config, n_bars=...)
        self.dataModule_ = dataModule
        self.dataModule_ = dataModule
        self.strategyModule_ = strategyModule
        self.feesModule_ = feesModule
        self.resultsModule_ = resultsModule
        self.vizModule_ = vizModule