# I.e., will the simulation be event-driven
# Can have the simulation be vectorized for simpler signal testing 

# TODO: Monte Carlo Path Generator?
import dataclasses

class BacktestConfig:
    def __init__(self, iterations, capital, fees, dates, seed):
        self.seed_       = seed # the random seed
        self.iterations_ = iterations # number of iterations
        self.capital_    = capital # starting capital
        self.fees_       = fees # transaction costs
        self.dates_      = dates # date range of simulation
