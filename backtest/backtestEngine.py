import numpy as np

from backtestConfig import BacktestConfig
from portfolioModule import Portfolio
from dataModule import DataModule
from executionModule import ExecutionModule
from strategyModule import StrategyModule
from resultsModule import ResultsModule
import vizModule


class BacktestEngine:
    def __init__(self, config: BacktestConfig, dataModule: DataModule,
                 strategyModule: StrategyModule, executionModule: ExecutionModule,
                 resultsModule: ResultsModule, vizModule):
        self.config = config
        self.dataModule_ = dataModule
        self.strategyModule_ = strategyModule
        self.executionModule_ = executionModule
        self.resultsModule_ = resultsModule
        self.vizModule_ = vizModule
        self.portfolio = None  # constructed in run(), once we know n_bars from real data

    def run(self):
        prices = self.dataModule_.load(
            self.config.start_date, self.config.end_date, self.config.rebalance_freq
        )
        self.portfolio = Portfolio(self.config, n_bars=len(prices))

        # TODO: the actual event loop.
        # for t, price in enumerate(prices):
        #     signal = self.strategyModule_.strategies[0].generate_signals(...)
        #     fill_price, cost = self.executionModule_.fill(order_size, price, adv=...)
        #     self.portfolio.apply_fill(fill_price, order_size)
        #     self.portfolio.mark_to_market(price)
        raise NotImplementedError


class ScenarioRunner:
    """Not needed yet — park this until a single BacktestEngine.run() call
    works end-to-end on one strategy. See config.n_simulations."""

    def __init__(self, config: BacktestConfig, engine_factory):
        self.config = config
        self.engine_factory = engine_factory  # callable that builds a fresh BacktestEngine

    def run(self) -> list[np.ndarray]:
        equity_curves = []
        for i in range(self.config.n_simulations):
            seed = self.config.seed + i if self.config.seed is not None else None
            engine = self.engine_factory(seed=seed)
            engine.run()
            equity_curves.append(engine.portfolio.equity_curve)
        return equity_curves