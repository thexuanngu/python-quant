"""
test_backtest.py: tests that actually run.

    python -m unittest -v test_backtest      (or:  pytest -v test_backtest.py)

Rules this file follows:
  * NO network. All prices are synthetic and seeded, so a failure is a bug, not Yahoo having a bad day.
  * Each test states a PROPERTY the engine must satisfy, not a number copied from a previous run.
  * Tests marked KNOWN BUG are expected to FAIL on code that still has the bug; they go green once fixed.
"""
import contextlib
import io
import unittest
import warnings
from datetime import date
from dataclasses import replace

import numpy as np
import pandas as pd

from backtestConfig import BacktestConfig
from backtestEngine import BacktestEngine
from executionModule import ExecutionModule
from portfolio_analytics import annualised_return, drawdown_stats, sharpe
from portfolioModule import Portfolio
from resultsModule import ResultsModule
from strategyModule import SMA, Strategy, StrategyModule, TrendPullback

CFG = BacktestConfig(start_date=date(2015, 1, 1), end_date=date(2026, 1, 1))

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------
def make_prices(n=1500, drift=0.0, vol=0.01, seed=0) -> pd.DataFrame:
    """Seeded log-random-walk with the two columns the engine needs."""
    rng = np.random.default_rng(seed)
    logp = np.cumsum(rng.normal(drift / 252, vol, n))
    return pd.DataFrame(
        {"target": 100.0 * np.exp(logp), "volume": rng.integers(1_000_000, 2_000_000, n).astype(float)},
        index=pd.bdate_range("2015-01-01", periods=n),
    )


class FakeData:
    """Stands in for DataModule: same .load() interface, no network."""
    def __init__(self, df): self.df = df
    def load(self, *_args): return self.df


class Constant(Strategy):
    def __init__(self, value):
        super().__init__(f"Const({value})"); self.value = value
    def generate_signals(self, data): return pd.Series(self.value, index=data.index, dtype=int)


class Pulse(Strategy):
    """+1 on exactly one bar k, 0 elsewhere. Used to check the one-bar execution lag."""
    def __init__(self, k):
        super().__init__(f"Pulse({k})"); self.k = k
    def generate_signals(self, data):
        s = pd.Series(0, index=data.index); s.iloc[self.k] = 1; return s


class Leaky(Strategy):
    """Deliberately uses the future (centred window). Exists to prove the lookahead test CAN fail."""
    def __init__(self, window=20):
        super().__init__("Leaky"); self.window = window
    def generate_signals(self, data):
        p = data["target"]
        return (p <= p.rolling(self.window, center=True).mean() * 0.99).astype(int)


def run_engine(df, strategy, fee_bps=0.0, slip_bps=0.0):
    engine = BacktestEngine(CFG, FakeData(df), StrategyModule([strategy]),
                            ExecutionModule(fee_bps, slip_bps), ResultsModule([]))
    return engine, engine.run()


def causality_violations(strategy, df, points=60, seed=0):
    """Times t where the signal computed from data[:t+1] differs from the full-data signal at t."""
    full = strategy.generate_signals(df)
    ts = np.random.default_rng(seed).integers(100, len(df), points)
    return [int(t) for t in ts if strategy.generate_signals(df.iloc[: t + 1]).iloc[-1] != full.iloc[t]]


def reference_sma_positions(price: pd.Series, window: int, thr: float) -> pd.Series:
    """Plain state machine: the slow, obviously-correct version of SMA's vectorised two-leg logic."""
    sma = price.shift(1).rolling(window).mean().to_numpy()
    p = price.to_numpy()
    pos, out = 0, np.zeros(len(p), dtype=int)
    for i in range(len(p)):
        if np.isnan(sma[i]):
            continue
        if pos == 1 and p[i] >= sma[i]: pos = 0
        if pos == -1 and p[i] <= sma[i]: pos = 0
        if pos == 0:
            if p[i] <= sma[i] * (1 - thr): pos = 1
            elif p[i] >= sma[i] * (1 + thr): pos = -1
        out[i] = pos
    return pd.Series(out, index=price.index)


# ----------------------------------------------------------------------------
# 1. Strategies
# ----------------------------------------------------------------------------
class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.df = make_prices(n=1200, seed=5)

    def test_signals_use_only_past_data(self):
        for s in (SMA(20, 0.02), TrendPullback(50, 10, 0.02)):
            with self.subTest(strategy=s.name):
                self.assertEqual(causality_violations(s, self.df), [])

    def test_lookahead_test_can_actually_fail(self):
        """A test that cannot fail proves nothing. A leaky strategy must be caught."""
        self.assertGreater(len(causality_violations(Leaky(), self.df)), 0)

    def test_sma_matches_reference_state_machine(self):
        for seed in (1, 2):
            price = make_prices(n=1500, seed=seed)["target"]
            for window, thr in [(10, 0.01), (20, 0.03), (50, 0.05)]:
                with self.subTest(seed=seed, window=window, thr=thr):
                    got = SMA(window, thr).generate_signals(price.to_frame("target"))
                    pd.testing.assert_series_equal(got, reference_sma_positions(price, window, thr),
                                                   check_names=False, check_dtype=False)

    def test_signals_are_valid_target_positions(self):
        for s in (SMA(20, 0.02), TrendPullback(50, 10, 0.02)):
            sig = s.generate_signals(self.df)
            self.assertTrue(set(sig.unique()) <= {-1, 0, 1})
            self.assertTrue((sig.iloc[:10] == 0).all(), "no signal before the warm-up window has filled")

    def test_bad_parameters_rejected(self):
        with self.assertRaises(ValueError): SMA(20, 0.0)
        with self.assertRaises(ValueError): TrendPullback(slowWindow=10, fastWindow=50, threshold=0.02)


# ----------------------------------------------------------------------------
# 2. Portfolio ledger
# ----------------------------------------------------------------------------
class TestPortfolio(unittest.TestCase):
    def test_equity_is_cash_plus_position_value(self):
        pf = Portfolio(CFG, n_bars=5)
        pf.apply_fill(100.0, 10.0, cost=2.0)
        self.assertAlmostEqual(pf.mark_to_market(105.0), pf.cash + pf.position * 105.0)

    def test_round_trip_pnl_and_fee_are_exact(self):
        pf = Portfolio(CFG, n_bars=5)
        pf.apply_fill(100.0, 10.0, cost=1.0)     # buy 10 @ 100, pay 1
        pf.apply_fill(110.0, -10.0, cost=1.0)    # sell 10 @ 110, pay 1
        self.assertAlmostEqual(pf.cash, CFG.initial_capital + 10 * 10 - 2.0)
        self.assertEqual(pf.position, 0.0)

    def test_short_profits_when_price_falls(self):
        pf = Portfolio(CFG, n_bars=5)
        pf.apply_fill(100.0, -10.0)
        self.assertGreater(pf.mark_to_market(90.0), CFG.initial_capital)

    def test_leverage_is_notional_over_equity(self):
        pf = Portfolio(CFG, n_bars=3)
        price = 250.0
        pf.apply_fill(price, CFG.initial_capital / price)
        pf.mark_to_market(price)
        self.assertAlmostEqual(pf.leverage, 1.0, places=6)


# ----------------------------------------------------------------------------
# 3. Engine
# ----------------------------------------------------------------------------
class TestEngine(unittest.TestCase):
    def setUp(self):
        self.df = make_prices(n=1500, seed=3)
        self.px = self.df["target"].to_numpy()

    def test_flat_strategy_keeps_capital(self):
        _, eq = run_engine(self.df, Constant(0), fee_bps=5, slip_bps=5)
        self.assertTrue(np.allclose(eq.to_numpy(), CFG.initial_capital))

    def test_buy_and_hold_reconciles_with_price(self):
        """With zero costs the engine's always-long equity must track price exactly (from the entry bar)."""
        _, eq = run_engine(self.df, Constant(1))
        np.testing.assert_allclose(eq.to_numpy()[1:] / eq.iloc[1], self.px[1:] / self.px[1], rtol=1e-9)
        # with costs: slightly below the frictionless result, but only by the one entry's friction (~1.5bp)
        _, eq_c = run_engine(self.df, Constant(1), fee_bps=1.0, slip_bps=0.5)
        shortfall = 1 - (eq_c.iloc[-1] / CFG.initial_capital) / (self.px[-1] / self.px[1])
        self.assertTrue(0 < shortfall < 3e-4, shortfall)

    def test_signal_is_executed_one_bar_later(self):
        """Signal known at the close of bar k can only be traded at bar k+1, never at k."""
        k = 100
        _, eq = run_engine(self.df, Pulse(k))
        self.assertAlmostEqual(eq.iloc[k + 1], CFG.initial_capital, places=6)       # entered at close k+1: no PnL yet
        self.assertAlmostEqual(eq.iloc[k + 2], CFG.initial_capital * self.px[k + 2] / self.px[k + 1], places=4)

    def test_higher_fees_never_help(self):
        finals = [run_engine(self.df, SMA(20, 0.02), fee_bps=f)[1].iloc[-1] for f in (0, 1, 5, 20)]
        self.assertTrue(all(a > b for a, b in zip(finals, finals[1:])), finals)

    def test_equity_has_no_nans(self):
        _, eq = run_engine(self.df, SMA(20, 0.02), fee_bps=1, slip_bps=0.5)
        self.assertFalse(eq.isna().any())

    def test_account_never_goes_negative(self):
        rising = make_prices(n=2000, drift=0.40, vol=0.30 / np.sqrt(252), seed=1)
        _, eq = run_engine(rising, Constant(-1), fee_bps=1, slip_bps=0.5)
        self.assertGreaterEqual(eq.min(), 0.0)
        
    def test_short_liquidation_closes_position(self):
        """Tests: 
        (1) Margin call actually occurs 
        (2) Liquidation has correct direction 
        (3) Portfolio ends flat and doesn't retain an unintended position
        """
        rising = make_prices(
            n=2000,
            drift=0.40,
            vol=0.30 / np.sqrt(252),
            seed=1
        )

        engine, eq = run_engine(rising, Constant(-1), fee_bps=1, slip_bps=0.5)

        liquidations = [
            trade for trade in engine.trades
            if trade[1] == "margin_liquidation"
        ]

        # A short must be bought back to liquidate.
        self.assertGreater(len(liquidations), 0)
        self.assertGreater(liquidations[0][2], 0)

        # The account must not retain an open position.
        self.assertAlmostEqual(engine.portfolio.position, 0.0)
        self.assertGreaterEqual(engine.portfolio.cash, 0.0)

        # Equity must never become negative under the broker-absorbs-deficit assumption.
        self.assertGreaterEqual(eq.min(), 0.0)
    
    def test_trade_log_records_signal_transitions(self):
        """Verify interaction between Strategy, BacktestEngine, and Portfolio"""
        k = 100
        engine, _ = run_engine(self.df, Pulse(k))

        signal_trades = [
            trade for trade in engine.trades
            if trade[1] == "signal"
        ]

        # Signal becomes active at k+1, then returns to flat at k+2.
        self.assertEqual([trade[0] for trade in signal_trades], [k + 1, k + 2])

        # First order buys; second order sells.
        self.assertGreater(signal_trades[0][2], 0)
        self.assertLess(signal_trades[1][2], 0)

        # The position should finish flat.
        self.assertAlmostEqual(engine.portfolio.position, 0.0)
        
    def test_long_liquidation_sells_to_close(self):
        """Verify long side liquidation"""
        cfg = replace(CFG, max_leverage=3.0)

        prices = pd.DataFrame({
            "target": [100.0, 100.0, 100.0, 50.0, 50.0],
            "volume": [1_000_000.0] * 5
        }, index=pd.bdate_range("2020-01-01", periods=5))

        engine = BacktestEngine(
            cfg,
            FakeData(prices),
            StrategyModule([Constant(1)]),
            ExecutionModule(0.0, 0.0),
            ResultsModule([])
        )

        eq = engine.run()

        liquidations = [
            trade for trade in engine.trades
            if trade[1] == "margin_liquidation"
        ]

        self.assertGreater(len(liquidations), 0)

        # A long must be sold to liquidate.
        self.assertLess(liquidations[0][2], 0)

        self.assertAlmostEqual(engine.portfolio.position, 0.0)
        self.assertGreaterEqual(eq.min(), 0.0)

# ----------------------------------------------------------------------------
# 4. Metrics
# ----------------------------------------------------------------------------
class TestMetrics(unittest.TestCase):
    def test_sharpe_matches_definition(self):
        r = np.random.default_rng(0).normal(0.0005, 0.01, 2000)
        self.assertAlmostEqual(sharpe(r), r.mean() / r.std(ddof=1) * np.sqrt(252))

    def test_max_drawdown_and_duration_on_known_curve(self):
        mdd, longest, _ = drawdown_stats([100, 120, 90, 110, 130])
        self.assertAlmostEqual(mdd, 90 / 120 - 1)
        self.assertEqual(longest, 2)             # bars 2 and 3 are below the 120 peak; bar 4 is a new high

    def test_drawdown_of_a_positive_curve_is_within_minus_100pct(self):
        eq = 100 * np.cumprod(1 + np.random.default_rng(1).normal(0, 0.02, 3000))
        self.assertGreaterEqual(drawdown_stats(eq)[0], -1.0)

    def test_annualised_return_of_a_total_loss_is_minus_one(self):
        """KNOWN BUG until fixed: a negative growth factor raised to a fractional power returns NaN.
        Length 5 matters: 252/5 = 50.4 is fractional. (Length 2 gives an even integer exponent, and a
        negative number to an even integer power is positive, which would hide the bug.)"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(annualised_return([-0.5, -1.2, 0.0, 0.0, 0.0]), -1.0)

    def test_results_module_prints_and_rejects_unknown_metrics(self):
        eq = pd.Series(100 * np.cumprod(1 + np.random.default_rng(2).normal(0.0005, 0.01, 300)),
                       index=pd.bdate_range("2020-01-01", periods=300))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ResultsModule(["sharpe", "drawdown"]).print_metrics(eq, 20)
        self.assertIn("Sharpe", buf.getvalue())
        with self.assertRaises(ValueError):
            ResultsModule(["bogus"]).print_metrics(eq)


if __name__ == "__main__":
    unittest.main(verbosity=2)