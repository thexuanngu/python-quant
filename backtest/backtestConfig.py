from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class BacktestConfig:
    """Immutable, loggable record of every knob for one run. 
    Frozen so a run can never be silently mutated mid-execution — 
    log this object alongside results so every equity curve is 
    reproducible from its config.
    """
    start_date:         date
    end_date:           date
    rebalance_freq:     str   = "1D"  # Pandas formatting
    initial_capital:    float = 1_000_000.0
    max_leverage:       float = 1.0  # how much current capital can be allocated 
    maintenance_margin: float = 0.25  # liquidate if equity < 25% of position notional
    fee_bps:            float = 1.0  # bps -> basis points (1bps = 0.01% = 0.0001)
    slippage_bps:       float = 0.5  # "price impact"
    n_simulations:      int   = 1  # >1 triggers a ScenarioRunner, not the Strategy
    seed:               int | None = None