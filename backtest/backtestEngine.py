import numpy as np
import pandas as pd

from backtestConfig import BacktestConfig
from portfolioModule import Portfolio
from dataModule import DataModule, CachedData
from executionModule import ExecutionModule
from strategyModule import StrategyModule, SingleWindowStrategy
from resultsModule import ResultsModule
# import vizModule


# TODO: Add Stop Loss
# TODO: Handle execution logic
# TODO: account for margin/borrow costs, short-sale constraints
# TODO: Intraday execution and latency
# TODO: Multiple assets and portfolio-level risk allocation
# TODO: Corporate-action cash-flow accounting
# TODO: More sophisticated order types and execution algorithms

class BacktestEngine:
    def __init__(self, config: BacktestConfig, dataModule: DataModule | CachedData,
                 strategyModule: StrategyModule, executionModule: ExecutionModule,
                 resultsModule: ResultsModule):
        self.config = config
        self.dataModule_ = dataModule
        self.strategyModule_ = strategyModule
        self.executionModule_ = executionModule
        self.resultsModule_ = resultsModule
        # self.vizModule_ = vizModule
        # self.portfolio = None  # constructed in run(), once we know n_bars from real data

    def run(self):
        # initialisation of data and portfolio
        c = self.config
        prices = self.dataModule_.load(c.start_date, c.end_date, c.rebalance_freq)
        px = prices['target'].to_numpy(np.float64)  # TODO: In the future, expand to multiple targets
        self.portfolio = pf = Portfolio(c, n_bars=len(px)) # TODO: Learn interaction between portfolio and multiple strategies
        
        # precompute signals here -> in the future, add some condition
        test_strat = self.strategyModule_.strategies[0]  # TODO: Expand to incorporate multiple strategies
        signals = test_strat.generate_signals(prices).shift(1).fillna(0).to_numpy()
        adv = prices['volume'].shift(1).rolling(window=  # TODO: In the future, make more generalizable
                                                test_strat.window if isinstance(test_strat, SingleWindowStrategy) 
                                                else 20).mean().to_numpy()
        prev = 0  # prev. position/signal
        self.trades = []  # log trades TODO: This could be used in ML models 
        
        for t in range(len(px)):  # iterate through time
            # check if we have to liquidate position first
            risk = abs(pf.position) * px[t]
            if risk > 0 and pf.equity(px[t]) < c.maintenance_margin * risk:
                self._trade(t, -pf.position, px[t], adv[t], "margin_liquidation")
                pf.cash = max(pf.cash, 0.0)  # broker will absorb all losses
                
            # there's been a signal change -> change position
            if prev != signals[t]:
                # size position
                units = signals[t] * c.max_leverage * max(pf.equity(px[t]), 0.0) / px[t]
                # trade position
                self._trade(t, units - pf.position, px[t], adv[t], "signal")
                # update current position
                prev = signals[t]  # update current position
            # build equity curve
            pf.mark_to_market(px[t])
        
        # return equity curve
        return pd.Series(pf.equity_curve, index=prices.index)
    
    def _trade(self, t, order, price, adv, reason):
            if order != 0:  
                fill_price, cost = self.executionModule_.fill(order, price, adv)
                self.portfolio.apply_fill(fill_price, order, cost)  # update portfolio
                self.trades.append((t, reason, order, fill_price, cost))  # update log
    
    def display_results(self, equity_curve: pd.Series, warmup: int = 0):
        self.resultsModule_.print_metrics(equity_curve, warmup)


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