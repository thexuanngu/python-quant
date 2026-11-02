import numpy as np
import pandas as pd
from datetime import date

from backtestConfig import BacktestConfig
from dataModule import DataModule, DataSource
from executionModule import ExecutionModule
from strategyModule import StrategyModule, SMA
from resultsModule import ResultsModule

from backtestEngine import BacktestEngine

def main():
    cfg = BacktestConfig(start_date=date(2015, 1, 1), end_date=date(2026, 1, 1))
    data = DataModule(DataSource("yfinance", "historical", ["AAPL"]))
    strategies = StrategyModule([SMA(window=20, threshold=0.03)])
    execution = ExecutionModule(cfg.fee_bps, cfg.slippage_bps)
    results = ResultsModule(["sharpe", "drawdown"])
    
    engine = BacktestEngine(cfg, data, strategies, execution, results)
    equity_curve = engine.run()
    engine.display_results(equity_curve, 20)

    
    
if __name__ == "__main__":
    main()