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
        self.portfolio = Portfolio(config, n_bars = 100, rebalanceFreq=2)
        self.dataModule_ = dataModule
        self.strategyModule_ = strategyModule
        self.executionModule_ = executionModule
        self.resultsModule_ = resultsModule
        self.vizModule_ = vizModule
        
class ScenarioRunner:
    def __init__(self, config: BacktestConfig, engine_factory):
        self.config = config
        self.engine_factory = engine_factory  # a function that builds a fresh BacktestEngine

    def run(self) -> list[np.ndarray]:
        equity_curves = []
        for i in range(self.config.iterations_):
            engine = self.engine_factory(seed=self.config.seed_ + i if self.config.seed_ else None)
            engine.run()
            equity_curves.append(engine.portfolio.equity_curve)
        return equity_curves