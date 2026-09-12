
class StrategyModule:
    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies # strategies to execute

class Strategy:
    def __init__(self, name: str):
        self.name = name # Name of strategy