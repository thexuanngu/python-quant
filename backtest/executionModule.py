from interfaces import ExecutionModelBase


class TransactionCost:
    def __init__(self, feeType: str):
        self.feeType = feeType  # "flat" or "percentage"


class ExecutionModule(ExecutionModelBase):
    def __init__(self, transactionCost: TransactionCost, priceImpact=None):
        self.transactionCost = transactionCost  # monetary cost of the trade
        self.priceImpact = priceImpact          # how the trade moves the price (optional for now)

    def fill(self, order_size: float, price: float, adv: float) -> tuple[float, float]:
        # TODO: apply self.transactionCost, then self.priceImpact (if set)
        # to get a realistic fill_price vs. the quoted `price`, and return
        # (fill_price, realized_cost). Start with transactionCost only —
        # add priceImpact once the flat-fee version runs end-to-end.
        raise NotImplementedError