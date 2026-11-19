# Project 0: Building a backtesting engine

## 'User Docs' (essentially the README.md)

*Questions to answer for self*

1. What did you build
2. Why did you build it
3. What mistakes did you make
4. If you could go back in time, what would you have done differently

The following excerpt presents the system design of the backtest engine.

![Current high-level system overview of base engine](image.png)

The graph depicts the various interactions of the `BacktestEngine` (BE) with its different 'modules'. Though not visibly apparent in the graph, the whole system is DAG-like because the BE can only run once the modules have been set up. For another visualisation, the BE is the orchestrator, and the various modules (i.e., `StrategyModule` (SM), `DataModule` (DM), `ExecutionModule` (EM) etc.) is the orchestra, each combining their unique parts to produce something the user can appreciate.

(With that being said, the `ResultsModule` (RM) is somewhat anomolous, as it TECHNICALLY does not need to reside within the BE, given its current role in the system).

As stated earlier, the modules are inputs into the BE, and the general data flow looks like:

DM -> SM -> `BacktestConfig` (BC) & EM -> RM -> BE  -> `VizModule` (VM)

(*Note at time of writing this, `VizModule` has not been implemented)

Putting the contrived chain into words:
1. `DataModule` loads and preprocesses data
2. `StrategyModule` contains various `Strategy` classes the user will implement to create a time series of desired exposure. It is important that the signals avoid look-ahead bias.
3. The `ExecutionModule` will determine the fill price (i.e., the asset purchase price) and the transaction cost of the trade.
    - Presently created with the `BacktestConfig`, with a simple flat fee structure
4. The `ResultsModule` displays portfolio analytics, such as sharpe, max drawdown, etc.
    - Right now it only prints numbers that can be used to (1) compare strategies and (2) build ML models/strats that use those metrics to guide their loss functtion.
5. The above modules then fees into the BE, via `.run()`  and displays the results at the end. 
    - At the beginning of `.run()`, a `Portfolio` is initialized to be the 'trading' account for the strat(s).
(Eventually, we would also have the visualisation module)

------

The next section will answer the following questions for each module:
1. **Purpose**: What is the point?
2. **Inputs**: What does this module receive?
3. **Outputs**: What does it guarantee to return
4. **State**: Does it maintain or mutate anything?
5. **Assumptions**: What must be true for its logic to work?
6. **Failure modes**: What happens when those assumptions are violated?

### `DataModule`
1. Retrieve, preprocess, and load the data for the BE
2. (currently limited to yfinance) ticker, date range, frequency
    - Future expansion: target columns, multiple tickers, data source
3. Processed `DataFrame` with standardised schema
4. Currently none; it retrieves data on demand
5. (currently) yfinance returns usable, consistently labeled historical data
6. Empty response, missing columns, malformed data

### `Strategy` (& `StrategyModule`)
1. Generates a signal (indication to buy/sell) (StrategyModule: container for multiple strategies—does not execute)
2. Processed `DataFrame` and strategy parameters (i.e,. window, threshold)
3. `pd.Series` representing the desired portfolio exposures/positions (-1, 0, or 1 for being short, flat, or long at specific points in time)
    - Currently computed via vectorization
    - Future expansion: strategy that is **event-driven**
    - `BacktestEngine` compares the desired exposure at each time step with the existing position and generates the corresponding order
4. Currently none; signals are computed once and then used
    - Future expansion: maintains a 'state' of the world that can inform trading decisions (i.e., the trade log) 
5. (For vectorization) the signal can be computed over arrays/Series and doesn't rely upon sequential runtime decisions.
6. Empty / Incomplete Series of Signals

### `BacktestConfig`
1. The static data for `BacktestEngine`—stores configs; provides parameters for initialisation
2. User-specified inputs for `DataModule`, `Portfolio`, `ExecutionModule`, and eventual `ScenarioRunner` (with `n_simulations`)
    - Future expansion: Eventually use the `seed` field meaningfully
3. An immutable (`@dataclass(frozen=True)`) and loggable record class for all of that information (with defaults for some missing inputs)
4. Maintains all the static information for the various modules
5. Assumes that the user provides sensible parameters (`BacktestConfig` can check types, but not values)
6. Unusable/ incomplete config properties (from poor user input); values with incorrect units, particularly the `_bps`,`max_leverage`, or `maintenance_margin` fields

### `ExecutionModule`
1. Handles execution logic, including the fill price (to use as a basis for returns) and the transaction cost (for the impact of the Portfolio), as prescribed from the strategy
    - Limitation -> doesn't handle partial fills or order rejection
2. The fee and sippage bps (supplied from `BacktestConfig`; currently flat), order quantity, listed asset price, and average daily volume
    - Future expansion: use ADV to realistically emulate the price impact of executing the trade; more dynamic `fee_bps` and `slippage_bps`; more metrics for execution; incorporate margin account calculation
3. The fill price and the transaction cost
    - Future expansion: more 'execution' quantities; make sure it's generalizable to multiple data sources
4. None currently; computes the transaction cost and fill price
5. All submitted orders are filled in full; ADV accepted byt not used; execution costs are modelled through fixed proportional slippage and commission.
6. Bad price and bad costs

### `BacktestEngine`
1. Runs the event loop, initializing a `Portfolio`, and handling the position sizing, logging the trades, and handling handling margin requirements
2. (after initializing the above, nothing else); additional result metrics would require the equity curve as a Series
3. A `pd.Series` of the marked-to-market equity curve indexed by price timestamps | printing out portfolio metrics
4. Maintains the trade logs; mutates the portfolio
5. The modules used in construction are well specified; data signals and execution calculations complete successfully.
6. Failure to run the test; bad equity curve; incoherent results

### `Portfolio`
1. Stateful accounting ledger to use as basis for strategy evaluation
2. `BacktestConfig` and the number of intervals of a single backtest run (agnostic to actual interval length)
3. Equity curve of the portfolio
4. The cash and the position will frequently mutate during the course of the backtest, along with the most recent price used to update the equity curve and the timestamp.
5. Uni-asset portfolio; the price, fill price, cost, and order are adequately supplied
    - Future: Expand to multi-asset
6. Nonsensical leverage / equity outputs

### `ResultsModule`
1. Displays metrics derived from the portfolio's equity curve
2. An equity curve (normally generated by the portfolio curve)
    - Future: Consider whether it's actually necessary to keep the `ResultsModule` baked inside the `BacktestEngine` (since the `display_results` is essentially a thin wrapper for the `print_metrics`)
3. Sharpe, Drawdown, annualized return etc.
4. Maintains the set of outputs the user wanted to see.
5. Valid equity curve
6. Nonsensical outputs.

---

(WIP) To describe some of the modules in more detail:
### DataModule
- Takes in a `DataSource` (which can be from a library  (i.e., `yfinance`), a CSV file, or some other source) and loads the data
    - Takes in 'data filters':
        - I.e., start date, end date, frequency, specific `yfTickers`
    - The `DataSource` is responsible for `preprocess_data()`, so the DataModule just has to load it
        - An essential step is to rename whatever target column we have to `target` (for SM)
- Anything data related (regarding loading and storing) should be handled in here: The rest of the engine should then only get clean, processed, ready to use data.

### StrategyModule
- Uses `generate_signals()` to inform the trading strategy
    
