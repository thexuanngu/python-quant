# 09/11/2026 (MM/DD/YYYY)
I have been inspired by this substack article to start working on my Python quantitative finance skills. In particular, given I'm kind of in a builder-y mood (with my C++ LOB that I'm slowly building out), this is a perfect opportunity to be greedy and do both.

While on the train home, I had a vision of what I wanted the back-testing engine to comprise of: 3 main 'input modules' (strategy, data, trade dynamics (like fees)) and 2 'output modules' (i.e., backtest results and visualization).

I'm pretty sure those will serve me well.
- SMA -> Simple Moving Average

# 09/21/2026
- `interfaces.py` enforces a standard structure for components
- Preallocating `_equity` in `portfolioModule.py` is efficient
- Frozen data class for `BacktestConfig` keeps configurations immutable and reproducible

I've asked both Gemini and Claude to help me with developing this backtest engine, and lowkey Claude is a lot more 'hands-on' compared to Gemini. What I will do is I will go through Gemini's comments first before Claude's. I need to actually resist the temptation to lazily copy-paste their responses. I need to read, internalize, then actually write the code myself.

I know people will go into a 'the age of AI' spiel, but I still believe that you don't truly understand something until you code it.

The 'Core Milestones' to complete are:
1. Implementing the event loop (a `run` method)
2. Building a Concrete Strategy 
3. Local Data Ingestion
4. Connect Execution and Portfolio

Afterwards, the next steps and 'core intuitions' are:
- Coding intuition (vectorization vs. Iteration)
- Financial Intuition (Market Friction)
- Math Intuition (Performance Metrics, Statistical Modeling)
- Data Integrity (Data Science)

- Then, determine whether there are specific performance metrics or technical indicators I want to implement in my very first strategy subclass

# 09/22/2026

Onto reviewing and understanding what Claude doesn't like with my current structures:
- Many bugs with the scaffold of my classes

I'll need to review all of the 'scaffolding' changes that Claude had provided, but I realize that this might have defeated the point: I'm supposed to be the one to wrangle with the scaffolding. I might play around later, look at it, before working on the next steps:
1. Implementing `DataSource.preprocess_data` and `DataModule.data_load` 
2. Write one `SMACrossover(Strategy)` subclass
3. Write the event loop in `BacktestEngine.run()`

# 09/24/2026

It is late, and the 'big' picture in my mind is cloudy--over the weekend I'll come back to this and start with fleshing out the `DataModule` methods.