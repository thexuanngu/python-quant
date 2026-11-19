import numpy as np
import pandas as pd
from datetime import date

from backtestConfig import BacktestConfig
from dataModule import DataModule, DataSource, CachedData
from executionModule import ExecutionModule
from strategyModule import StrategyModule, SMA
from resultsModule import ResultsModule
from portfolio_analytics import sharpe, drawdown_stats

from backtestEngine import BacktestEngine

def main():
    cfg = BacktestConfig(start_date=date(2015, 1, 1), end_date=date(2026, 1, 1))
    execution = ExecutionModule(cfg.fee_bps, cfg.slippage_bps)
    results = ResultsModule(["sharpe", "drawdown", "sortino","vol", "return", "calmar"])
    
    # simple parameter grid:
    rows = []
    for t in ["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "GS"]:
        # get the data then cache
        data = DataModule(DataSource("yfinance", "historical", [t]))
        cache = CachedData(data.load(cfg.start_date, cfg.end_date, cfg.rebalance_freq))
    
        for w in [10, 20, 50, 100, 200]:
            for th in [0.005, 0.01, 0.03, 0.05, 0.1]:
                strategies = StrategyModule([SMA(window=w, threshold=th)])
        
                print("#" + 20 * "-" + f"{t}—Window: {w} | Threshold: {th}" + 20 * "-" + "#")
                engine = BacktestEngine(cfg, cache, strategies, execution, results)
                eq = engine.run()
                engine.display_results(eq, w)
                print("#" + 71 * "-" + "#")
                mdd, longest, _ = drawdown_stats(eq)
                rows.append({"ticker": t, "window": w, "thr": th, "sharpe": sharpe(eq.pct_change().dropna().to_numpy()), "maxdd": mdd,
             "trades": len(engine.trades), "ruined": bool(eq.min() <= 0)})
                
                
    pd.DataFrame(rows).pivot_table(index="window", columns="thr", values="sharpe")
            
if __name__ == "__main__":
    main()