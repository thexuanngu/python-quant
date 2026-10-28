import numpy as np

from backtestConfig import BacktestConfig
from portfolioModule import Portfolio
from dataModule import DataModule
from executionModule import ExecutionModule
from strategyModule import StrategyModule
from resultsModule import ResultsModule
# import vizModule

import pandas as pd

# TODO: Add Stop Loss
# TODO: Handle execution logic
# TODO: account for margin/borrow costs

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
        c = self.config
        prices = self.dataModule_.load(c.start_date, c.end_date, c.rebalance_freq)
        px = prices['target'].to_numpy(np.float64)
        self.portfolio = pf = Portfolio(c, n_bars=len(px))
        
        # precomputation (happens once)
        signals = self.strategyModule_.strategies[0].generate_signals(prices)
        target  = signals.shift(1).fillna(0).to_numpy(np.float64)  # positions we want to maintain
        adv     = prices["volume"].shift(1).rolling(20).mean().to_numpy()
        
        prev = 0  # start off in "flat" position
        for t in range(len(px)):
            if target[t] != prev:
                units = target[t] * c.max_leverage * pf.equity(px[t]) / px[t]
                order = units - pf.position
            
                fill_price, cost = self.executionModule_.fill(order, px[t], adv[t])
                self.portfolio.apply_fill(fill_price, order, cost)
                prev = target[t]
            self.portfolio.mark_to_market(px[t])
        return pd.Series(pf.equity_curve, index=prices.index)


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