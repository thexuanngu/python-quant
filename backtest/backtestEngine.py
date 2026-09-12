from backtestConfig import BacktestConfig
from portfolioModule import Portfolio
from dataModule import DataModule
import resultsModule
import backtest.executionModule as executionModule
import strategyModule
import vizModule
import numpy as np

@dataclass(frozen=True)
class BacktestConfig:
    """Immutable, loggable record of every knob for one run. Frozen so a run
    can never be silently mutated mid-execution — log this object alongside
    results so every equity curve is reproducible from its config."""
    start_date: date
    end_date: date
    initial_capital: float = 1_000_000.0
    rebalance_freq: str = "1D"
    max_leverage: float = 1.0
    fee_bps: float = 1.0
    slippage_bps: float = 0.5
    n_simulations: int = 1          # >1 triggers a ScenarioRunner, not the Strategy
    seed: int | None = None

class ScenarioRunner:
    def __init__(self, config: BacktestConfig, engine_factory):
        self.config = config
        self.engine_factory = engine_factory  # a function that builds a fresh BacktestEngine

    def run(self) -> list[np.ndarray]:
        equity_curves = []
        for i in range(self.config.n_simulations):
            engine = self.engine_factory(seed=self.config.seed + i if self.config.seed else None)
            engine.run()
            equity_curves.append(engine.portfolio.equity_curve)
        return equity_curves

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