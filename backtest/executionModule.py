
class ExecutionModule:
    def __init__(self, transactionCost: TransactionCost):
        self.transactionCost = transactionCost # How much does it monetarily cost to execute the trade
        self.priceImpact = priceImpact # How does this affect the price of this asset?

class TransactionCost:
    def __init__(self, feeType):
        self.feeType = feeType # I.e., for each trade, will it be a flat fee or percentage based?