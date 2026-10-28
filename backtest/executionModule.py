from interfaces import ExecutionModelBase
import numpy as np


# class TransactionCost:
#     def __init__(self, feeType: str):
#         self.feeType = feeType  # "flat" or "percentage"


# class ExecutionModule(ExecutionModelBase):
#     def __init__(self, transactionCost: TransactionCost, priceImpact=None):
#         self.transactionCost = transactionCost  # monetary cost of the trade
#         self.priceImpact = priceImpact          # how the trade moves the price (optional for now)

# 1e-4 to correctly convert it into a decimal
class ExecutionModule(ExecutionModelBase):
    def __init__(self, fee_bps: float, slippage_bps: float):
        self.fee, self.slip = fee_bps * 1e-4, slippage_bps * 1e-4


    def fill(self, order_size: float, price: float, adv: float) -> tuple[float, float]:
        # TODO: apply self.transactionCost, then self.priceImpact (if set)
        # to get a realistic fill_price vs. the quoted `price`, and return
        # (fill_price, realized_cost). Start with transactionCost only —
        # add priceImpact once the flat-fee version runs end-to-end.
        
        # simple case: the transactionCost -> config's fee_bps;
        # priceImpact -> config's slippage_bps
        fill_price = price * (1 + np.sign(order_size) * self.slip)   # buys fill higher (asks), sells lower
        return fill_price, abs(order_size) * fill_price * self.fee
        
        