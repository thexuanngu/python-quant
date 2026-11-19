# Mistakes 

- Negative equity -> produces NaNs (fractional powers on negative numbers)
- Did not implement maintenance margin (if equity is negative)

- Not correctly setting up the main (i.e., not writing if `__name__ == "__main__":`)
- naming conventions across library (i.e., pandas using "1D" whereas yfinance uses "1d")
- Cache the data first -- quicker data reads 
- forget to call `.mean()` after rolling
- To liquidate (`"margin_liquidation"`), I need to trade $-q$, not $q$
- The `signals` in the engine also need to be shifted by 1: we only have information available from $t-1$. 
    - Correct way to approach it is (1) calculate signal from close $t$ (i.e., t-1) and (2) execute signal at next bar
    - In the case of SMA, for a decision at $t$, the signal is computed at $t-1$. At $t-1$, the SMA is from $t-2$ onwards. Only at the end of the day, do we observe $t-1$. Therefore, at the end of the day, we have an idea of what we're supposed to do.
- Handle division by zero possibilities 
- Bad data isn't just missing or not formatted correctly, but also NaNs, missing, or negative prices
- Convert the pandas Series into numpy arrays (for safe integer-indexing)