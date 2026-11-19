"""
portfolio_analytics.py: instructor solutions for the Portfolio Analytics study plan.

Every function is a pure function of arrays/Series (no state), so it can drop
straight into resultsModule. Run `python portfolio_analytics.py` to execute the
self-checks at the bottom; each one asserts a property you should be able to
explain out loud in an interview.

Conventions: returns are simple per-period returns; `periods` is bars per year
(252 daily); rf is an ANNUAL rate; kurtosis is NON-excess (normal = 3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.covariance import LedoitWolf

TRADING_DAYS = 252
EULER_MASCHERONI = 0.5772156649015329

# ============================================================================
# 1. Performance and drawdown
# ============================================================================
#TODO: Understand and reimplement all of the methods. Current: 0/20
def annualised_return(r, periods: int = TRADING_DAYS) -> float:
    """Geometric (compounded) annual return (CAGR). Arithmetic mean * periods overstates it."""
    r = np.asarray(r, dtype=float)
    growth = np.prod(1.0 + r)
    return float(growth ** (periods / len(r)) - 1.0) if growth > 0 else -1.0 


def annualised_vol(r, periods: int = TRADING_DAYS) -> float:
    return float(np.std(r, ddof=1) * np.sqrt(periods))


def sharpe(r, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Annualised Sharpe. The sqrt(periods) scaling assumes iid returns; with
    positive autocorrelation it overstates (Lo 2002)."""
    ex = np.asarray(r, dtype=float) - rf / periods
    return float(ex.mean() / ex.std(ddof=1) * np.sqrt(periods))


def sortino(r, mar: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Downside deviation is computed over ALL observations (negatives kept,
    positives floored at 0), not just over the negative ones."""
    ex = np.asarray(r, dtype=float) - mar / periods
    downside = np.sqrt(np.mean(np.minimum(ex, 0.0) ** 2))
    return float(ex.mean() / downside * np.sqrt(periods))


def drawdown_stats(equity) -> tuple[float, int, np.ndarray]:
    """Return (max drawdown as a negative fraction, longest underwater spell in
    bars, full drawdown series). O(n), fully vectorised."""
    eq = np.asarray(equity, dtype=float)
    dd = eq / np.maximum.accumulate(eq) - 1.0
    under = np.concatenate(([0], (dd < 0).astype(np.int8), [0]))
    edges = np.flatnonzero(np.diff(under))          # alternating start/end of spells
    spells = edges[1::2] - edges[::2]
    return float(dd.min()), int(spells.max()) if spells.size else 0, dd


def calmar(equity, periods: int = TRADING_DAYS) -> float:
    """Calmar Ratio. Risk-adjusted performance metric that measures a portfolio's
    Compound Annual Growth Rate (CAGR; annualized return) relative to its maximum
    drawdown."""
    eq = np.asarray(equity, dtype=float)
    r = eq[1:] / eq[:-1] - 1.0
    mdd, _, _ = drawdown_stats(eq)
    return float(annualised_return(r, periods) / abs(mdd))


# ============================================================================
# 2. Is the Sharpe real? (inference, not just a point estimate)
# ============================================================================
def sharpe_se(sr: float, n: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Std error of a PERIODIC (un-annualised) Sharpe (Mertens 2002). With
    skew=0, kurt=3 it reduces to the iid result sqrt((1 + SR^2/2)/(n-1))."""
    return float(np.sqrt((1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2) / (n - 1)))


def probabilistic_sharpe(r, sr_benchmark: float = 0.0) -> float:
    """P(true periodic Sharpe > benchmark), correcting for sample length,
    skew and fat tails (Bailey & Lopez de Prado)."""
    r = np.asarray(r, dtype=float)
    sr = r.mean() / r.std(ddof=1)
    se = sharpe_se(sr, len(r), float(stats.skew(r)), float(stats.kurtosis(r, fisher=False)))
    return float(stats.norm.cdf((sr - sr_benchmark) / se))


def deflated_sharpe(r, trial_sr_var: float, n_trials: int) -> float:
    """PSR against the Sharpe you'd expect from the BEST of n_trials pure-noise
    strategies. `trial_sr_var` = variance of the periodic Sharpes across trials.
    This is the multiple-testing correction for 'I tried 50 parameter sets'."""
    z = stats.norm.ppf
    sr0 = np.sqrt(trial_sr_var) * ((1 - EULER_MASCHERONI) * z(1 - 1 / n_trials)
                                   + EULER_MASCHERONI * z(1 - 1 / (n_trials * np.e)))
    return probabilistic_sharpe(r, sr_benchmark=sr0)


def bootstrap_sharpe_ci(r, block: int = 20, n_boot: int = 2000, alpha: float = 0.05,
                        periods: int = TRADING_DAYS, seed: int = 0) -> tuple[float, float]:
    """Circular block bootstrap CI for the annualised Sharpe. Blocks preserve
    short-range autocorrelation/vol clustering that an iid resample destroys."""
    r = np.asarray(r, dtype=float)
    n = len(r)
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(n_boot, n_blocks))
    idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(n_boot, -1)[:, :n]
    s = r[idx]
    srs = s.mean(axis=1) / s.std(axis=1, ddof=1) * np.sqrt(periods)
    lo, hi = np.quantile(srs, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


# ============================================================================
# 3. CAPM / single-factor regression
# ============================================================================
def capm(asset, market, rf: float = 0.0, periods: int = TRADING_DAYS) -> dict:
    """OLS of excess asset returns on excess market returns.
    r_i - rf = alpha + beta (r_m - rf) + eps.  beta = Cov(r_i, r_m) / Var(r_m)."""
    y = np.asarray(asset, dtype=float) - rf / periods
    x = np.asarray(market, dtype=float) - rf / periods
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    n, k = X.shape
    s2 = resid @ resid / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    return {
        "alpha_ann": float(coef[0] * periods), "beta": float(coef[1]),
        "t_alpha": float(coef[0] / se[0]), "t_beta": float(coef[1] / se[1]),
        "r2": float(1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))),
        "resid_vol_ann": float(np.sqrt(s2 * periods)),
        "info_ratio": float(coef[0] * periods / np.sqrt(s2 * periods)),
    }


# ============================================================================
# 4. Mean-variance optimisation (and why it misbehaves)
# ============================================================================
def min_variance_weights(cov) -> np.ndarray:
    """w = S^-1 1 / (1' S^-1 1). Needs NO expected returns, hence much more robust."""
    w = np.linalg.solve(cov, np.ones(len(cov)))
    return w / w.sum()


def tangency_weights(mu, cov, rf: float = 0.0) -> np.ndarray:
    """Max-Sharpe fully-invested portfolio: w proportional to S^-1 (mu - rf)."""
    w = np.linalg.solve(cov, np.asarray(mu) - rf)
    return w / w.sum()


def efficient_frontier(mu, cov, n_points: int = 50, span: tuple[float, float]=(-0.5, 1.5)):
    """Two-fund theorem: every frontier portfolio is a mix of two frontier
    portfolios. Returns (vols, rets, weights) for mixes of min-var and tangency."""
    w_mv, w_tan = min_variance_weights(cov), tangency_weights(mu, cov)
    lam = np.linspace(*span, n_points)[:, None]
    W = w_mv + lam * (w_tan - w_mv)
    return np.sqrt(np.einsum("ij,jk,ik->i", W, cov, W)), W @ mu, W


def weight_instability(returns: pd.DataFrame, n_boot: int = 300, seed: int = 0,
                       shrink_cov: bool = False) -> pd.DataFrame:
    """Std of each asset's weight across bootstrap resamples of the SAME data.
    Large std = the optimiser is fitting noise in the estimates."""
    rng = np.random.default_rng(seed)
    X = returns.to_numpy()
    n = len(X)
    tan, mv = [], []
    for _ in range(n_boot):
        s = X[rng.integers(0, n, n)]
        mu = s.mean(axis=0)
        cov = LedoitWolf().fit(s).covariance_ if shrink_cov else np.cov(s, rowvar=False)
        tan.append(tangency_weights(mu, cov))
        mv.append(min_variance_weights(cov))
    return pd.DataFrame({"tangency_w_std": np.std(tan, axis=0),
                         "minvar_w_std": np.std(mv, axis=0)}, index=returns.columns)


# ============================================================================
# 5. Tail risk and volatility targeting
# ============================================================================
def var_cvar_historical(r, level: float = 0.99) -> tuple[float, float]:
    """(VaR, CVaR) as positive loss fractions. CVaR = mean loss beyond VaR."""
    r = np.asarray(r, dtype=float)
    q = np.quantile(r, 1 - level)
    return float(-q), float(-r[r <= q].mean())


def var_cvar_normal(r, level: float = 0.99) -> tuple[float, float]:
    """Gaussian VaR/CVaR from the sample mean and std. Understates the extreme
    tail whenever returns are fat-tailed."""
    r = np.asarray(r, dtype=float)
    mu, sd, a = r.mean(), r.std(ddof=1), 1 - level
    z = stats.norm.ppf(a)
    return float(-(mu + sd * z)), float(-mu + sd * stats.norm.pdf(z) / a)


def vol_target(r: pd.Series, target: float = 0.10, span: int = 60, cap: float = 3.0,
               periods: int = TRADING_DAYS) -> tuple[pd.Series, pd.Series]:
    """Scale exposure inversely to recent EWMA vol. The shift(1) is essential:
    leverage for bar t may only use returns up to t-1, otherwise it is lookahead."""
    vol = r.ewm(span=span, min_periods=span).std() * np.sqrt(periods)
    lev = (target / vol).clip(upper=cap).shift(1)
    return (lev * r).dropna(), lev.dropna()


# ============================================================================
# 6. Correlation structure
# ============================================================================
def effective_num_bets(cov_or_corr) -> float:
    """exp(entropy of the normalised eigenvalue spectrum). 1 if everything is one
    bet, N if the assets are uncorrelated and equal variance."""
    lam = np.clip(np.linalg.eigvalsh(cov_or_corr), 1e-12, None)
    p = lam / lam.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def avg_pairwise_corr(returns: pd.DataFrame) -> float:
    c = returns.corr().to_numpy()
    return float(c[np.triu_indices_from(c, k=1)].mean())


# ============================================================================
# Self-checks: each assert is a statement you should be able to defend.
# ============================================================================
if __name__ == "__main__":
    rng = np.random.default_rng(42)
    n = 2520
    print("running self-checks...\n")

    # --- 1. metrics ---------------------------------------------------------
    r = rng.normal(0.0004, 0.01, n)
    eq = 100 * np.cumprod(1 + r)
    ref_sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
    assert np.isclose(sharpe(r), ref_sr)
    mdd, longest, dd = drawdown_stats(eq)
    peak, ref_mdd, cur, ref_longest = -np.inf, 0.0, 0, 0   # brute-force loop reference
    for v in eq:
        peak = max(peak, v); ref_mdd = min(ref_mdd, v / peak - 1)
        cur = cur + 1 if v < peak else 0; ref_longest = max(ref_longest, cur)
    assert np.isclose(mdd, ref_mdd) and longest == ref_longest
    print(f"[1] Sharpe {sharpe(r):.2f} | Sortino {sortino(r):.2f} | maxDD {mdd:.1%} | longest underwater {longest} bars | Calmar {calmar(eq):.2f}")

    # --- 2. Sharpe inference ------------------------------------------------
    lo, hi = bootstrap_sharpe_ci(r)
    assert lo < sharpe(r) < hi
    se_gauss = sharpe_se(0.05, 1000)
    assert np.isclose(se_gauss, np.sqrt((1 + 0.5 * 0.05 ** 2) / 999))
    noise = rng.normal(0, 0.01, n)                     # zero true edge
    trials = np.array([rng.normal(0, 0.01, n) for _ in range(100)])
    best = trials[np.argmax(trials.mean(1) / trials.std(1, ddof=1))]
    sr_var = np.var(trials.mean(1) / trials.std(1, ddof=1), ddof=1)
    psr_best, dsr_best = probabilistic_sharpe(best), deflated_sharpe(best, sr_var, 100)
    assert dsr_best < psr_best
    print(f"[2] Sharpe 95% block-bootstrap CI ({lo:.2f}, {hi:.2f}) | best-of-100 pure-noise strategy: PSR {psr_best:.2f} -> DSR {dsr_best:.2f}")

    # --- 3. CAPM vs an independent implementation -----------------------------
    mkt = rng.normal(0.0004, 0.01, n)
    asset = 0.0002 + 1.3 * mkt + rng.normal(0, 0.008, n)
    c = capm(asset, mkt)
    lr = stats.linregress(mkt, asset)
    assert np.isclose(c["beta"], lr.slope) and np.isclose(c["alpha_ann"], lr.intercept * 252)
    assert np.isclose(c["t_beta"], lr.slope / lr.stderr) and np.isclose(c["t_alpha"], lr.intercept / lr.intercept_stderr)
    assert np.isclose(c["beta"], np.cov(asset, mkt)[0, 1] / np.var(mkt, ddof=1))
    print(f"[3] beta {c['beta']:.2f} (t={c['t_beta']:.0f}) | alpha {c['alpha_ann']:.2%}/yr (t={c['t_alpha']:.2f}) | R2 {c['r2']:.2f}")

    # --- 4. mean-variance ------------------------------------------------------
    k = 6
    A = rng.normal(0, 0.003, (k, k)); cov_true = A @ A.T + np.diag(np.full(k, 1e-4)) + 4e-5
    mu_true = np.array([0.0003, 0.0004, 0.0002, 0.0005, 0.0003, 0.0004])
    R = pd.DataFrame(rng.multivariate_normal(mu_true, cov_true, 750), columns=list("ABCDEF"))  # ~3y daily
    mu, cov = R.mean().to_numpy(), R.cov().to_numpy()
    w_mv, w_tan = min_variance_weights(cov), tangency_weights(mu, cov)
    assert np.isclose(w_mv.sum(), 1) and np.isclose(w_tan.sum(), 1)
    ew = np.full(k, 1 / k)
    assert w_mv @ cov @ w_mv <= ew @ cov @ ew
    sr_of = lambda w: (w @ mu) / np.sqrt(w @ cov @ w)
    assert sr_of(w_tan) >= sr_of(w_mv) - 1e-12
    vols, rets, _ = efficient_frontier(mu, cov)
    inst = weight_instability(R)
    inst_lw = weight_instability(R, shrink_cov=True)
    assert inst["tangency_w_std"].mean() > inst["minvar_w_std"].mean()
    print(f"[4] in-sample Sharpe: tangency {sr_of(w_tan)*np.sqrt(252):.2f} vs min-var {sr_of(w_mv)*np.sqrt(252):.2f}")
    print(f"    avg weight std across bootstraps: tangency {inst['tangency_w_std'].mean():.2f} | min-var {inst['minvar_w_std'].mean():.2f}"
          f" | min-var + Ledoit-Wolf {inst_lw['minvar_w_std'].mean():.2f}")

    # --- 5. tail risk and vol targeting -------------------------------------------
    t3 = rng.standard_t(3, 500_000) / np.sqrt(3) * 0.01        # unit-variance fat tails
    h_var, h_cvar = var_cvar_historical(t3, 0.99)
    n_var, n_cvar = var_cvar_normal(t3, 0.99)
    assert h_cvar > h_var and n_var < h_var and n_cvar < h_cvar
    h95, _ = var_cvar_historical(t3, 0.95); n95, _ = var_cvar_normal(t3, 0.95)
    assert n95 > h95                                         # at 95% the normal OVERstates
    print(f"[5] fat-tailed returns, 99%: hist VaR {h_var:.2%} / CVaR {h_cvar:.2%} vs normal VaR {n_var:.2%} / CVaR {n_cvar:.2%}"
          f" | at 95% normal VaR {n95:.2%} vs hist {h95:.2%}")
    vol_path = np.where(np.arange(n) % 500 < 250, 0.006, 0.020)        # calm / turbulent regimes
    rr = pd.Series(rng.normal(0.0003, 1, n) * vol_path)
    vt, lev = vol_target(rr, target=0.12)
    raw_roll = rr.rolling(63).std().dropna() * np.sqrt(252)
    vt_roll = vt.rolling(63).std().dropna() * np.sqrt(252)
    assert vt_roll.std() < raw_roll.std()
    print(f"    rolling-vol dispersion: raw {raw_roll.std():.3f} -> vol-targeted {vt_roll.std():.3f} (avg leverage {lev.mean():.2f})")

    # --- 6. correlation structure -----------------------------------------------------
    assert np.isclose(effective_num_bets(np.eye(8)), 8)
    assert np.isclose(effective_num_bets(np.ones((8, 8)) + 1e-9 * np.eye(8)), 1, atol=1e-3)
    f = rng.normal(0, 0.01, (n, 1))
    X = pd.DataFrame(0.8 * f + rng.normal(0, 0.006, (n, 8)))
    print(f"[6] one-factor world, 8 assets: avg pairwise corr {avg_pairwise_corr(X):.2f} -> effective independent bets {effective_num_bets(X.corr().to_numpy()):.1f} (not 8)")
    print("\nall checks passed")
