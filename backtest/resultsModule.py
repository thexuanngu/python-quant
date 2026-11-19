import pandas as pd
from portfolio_analytics import drawdown_stats, sharpe, sortino, annualised_return, annualised_vol, calmar

#TODO: Sharpe Ratio, Max Drawdown, other metrics
#TODO: Make sure the metrics that perform division are not dividing by 0 (i.e., check for degenerate outputs)
class ResultsModule:
    def __init__(self, metrics: list[str]):
        self.metrics = [m.lower() for m in metrics]
        
    def print_metrics(self, equity_curve: pd.Series, warmup: int = 0) -> None:
        eq = equity_curve[warmup:]
        r = eq.pct_change().dropna().to_numpy()  # numpy for faster computation
        for m in self.metrics:
            match m:
                case "drawdown":
                    mdd, longest, _ = drawdown_stats(eq.to_numpy())
                    print(f"Max drawdown: {mdd:.1%} | longest underwater: {longest} bars")
                case "sharpe":
                    print(f"Sharpe (ann.): {sharpe(r):.2f}")
                case "sortino":
                    print(f"Sortino: {sortino(r):.2f}")
                case "return":
                    print(f"Return (ann.): {annualised_return(r) * 100 :.2f}%")
                case "vol":
                    print(f"Vol (ann.): {annualised_vol(r) * 100 :.2f}%")
                case "calmar":
                    print(f"Calmar (ann.): {calmar(eq.to_numpy()):.2f}")
                case _:
                    raise ValueError(f"Unknown metric: {m}")