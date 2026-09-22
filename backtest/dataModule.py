import pandas as pd

class DataSource:
    def __init__(self, source, nature):
        self.source = source # I.e., where does the data come from? (yfinance, static, live etc.)
        self.nature = nature # I.e., is the data live?

class DataModule:
    def __init__(self, dataSource: DataSource):
        self.dataSource = dataSource


