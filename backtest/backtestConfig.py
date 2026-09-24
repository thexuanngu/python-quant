from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BacktestConfig:
    """Immutable, loggable record of every knob for one run. Frozen so a run
    can never be silently mutated mid-execution — log this object alongside
    results so every equity curve is reproducible from its config.
    """
    start_date:      date
    end_date:        date
    initial_capital: float = 1_000_000.0
    rebalance_freq:  str = "1D"
    max_leverage:    float = 1.0
    fee_bps:         float = 1.0
    slippage_bps:    float = 0.5
    n_simulations:   int = 1          # >1 triggers a ScenarioRunner, not the Strategy
    seed:            int | None = None