# Project 0: Building a backtesting engine

## 'User Docs' (essentially the README.md)

The following excerpt shall present the system design of the backtest engine.

![Current high-level system overview of base engine](image.png)

The graph above depicts the various interactions of the `BacktestEngine` (BE) with its different 'modules'—particularly how the modules comprise the engine. Though not visibly apparent in the graph, the whole system is DAG-like because the BE can only run once the modules have been set up. For another visualisation, the BE is the orchestrator, and the various modules (i.e., `StrategyModule` (SM), `DataModule` (DM), `ExecutionModule` (EM) etc.) is the orchestra, each combining their unique parts to produce something the user can appreciate.

(With that being said, the `ResultsModule` (RM) is somewhat anomolous, as it TECHNICALLY does not need to reside within the BE, given its current role in the system. However, as I familiarise myself with the machinery in this repo, it's possible the RM will become more integral for the functioning of the BE).

As stated earlier, the modules are inputs into the BE, and the general data flow looks like:

DM -> SM -> `BacktestConfig` (BC) & EM -> RM -> BE  -> `VizModule` (VM)

(*Note at time of writing this, `VizModule` has not really been implemented)

Putting the contrived chain into words:
1. Data is loaded (from a user-specified source) and preprocessed within the `DataModule`
2. The `StrategyModule`, under some assumptions on the format of the data it will receive, contains various `Strategy` classes the user will design to `generate_signals()`. It is important that the signals avoid look-ahead bias.
3. The `ExecutionModule` is presently created with the `BacktestConfig` supplying essential fields
    - In the future, the `BacktestConfig` will likely play a bigger role in essentially setting everything up from the get go.
4. The final important module to plug in is then the `ResultsModule`, which will display some of the Portfolio analytics, such as sharpe, max drawdown, etc.
    - While right now it's just used to print a number, in the future, it can be used to (1) help compare strategies and (2) to build machine learning models/strategies that will use some of the metrics the RM can produce to guide its loss functtion.
5. All of the above then feeds into the BE, which calls `.run()` (using all of its internally loaded modules) and displays the results at the end. It also loads up its own `PortfolioModule` to be our 'trading' account for our strategy.
    - The portfolio is where the strategy is executed.
(Eventually, we would also have the visualisation module)

To describe some of the modules in more detail:
### DataModule
- Takes in a `DataSource` (which can be from a library  (i.e., `yfinance`), a CSV file, or some other source) and loads the data
    - Takes in 'data filters':
        - I.e., start date, end date, frequency, specific `yfTickers`
    - The `DataSource` is responsible for `preprocess_data()`, so the DataModule just has to load it
        - An essential step is to rename whatever target column we have to `target` (for SM)
- Anything data related (regarding loading and storing) should be handled in here: The rest of the engine should then only get clean, processed, ready to use data.

###
    
