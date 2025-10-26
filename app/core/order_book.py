from decimal import Decimal
from collections import deque
from sortedcontainers import SortedDict
from typing import Deque
from app.core.order_types import Order, Side
from dataclasses import dataclass

@dataclass
class PriceLevel:
    price: Decimal
    total_qty: Decimal
    orders: Deque[Order]

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # Ascending order of prices
        # bids: use SortedDict where highest key is best bid
        self.bids: SortedDict[Decimal, PriceLevel] = SortedDict()
        # asks: lowest key is best ask
        self.asks: SortedDict[Decimal, PriceLevel] = SortedDict()

    def add_limit_order(self, order: Order):
        """
        This function adds LIMIT order types. It creates an entry if the price is not the key in dictionary.\n
        Else, if the entry for price is found, it appends this order inside orders queue and increments total_qty.
        """
        side_dict = self.bids if order.side == Side.BUY else self.asks
        price = order.price
        if price not in side_dict:
            side_dict[price] = PriceLevel(price, Decimal('0'), deque())
        level = side_dict[price]
        level.orders.append(order)
        level.total_qty += order.quantity

    def get_bbo(self):
        best_bid = None
        best_ask = None
        if len(self.bids):
            # As orders are sorted in ascending order of prices, highest bid is at the end
            best_bid = self.bids.peekitem(-1)[0]
        if len(self.asks):
            best_ask = self.asks.peekitem(0)[0]
        return best_bid, best_ask

    def top_n(self, n=10):
        asks = []
        bids = []
        for price, lvl in list(self.asks.items())[:n]:
            asks.append((str(price), str(lvl.total_qty)))
        for price, lvl in list(self.bids.items())[-n:]:
            bids.insert(0, (str(price), str(lvl.total_qty)))
        return asks, bids
    
    def get_depth(self, side: str, levels: int = 10):
        """
        Returns top N price levels for the given side (buy/sell).
        Returns list of tuples: (price, total_quantity)
        """
        book = self.bids if side == "buy" else self.asks
        depth = []
        count = 0
        for price, orders in book.items():
            total_qty = sum(o.quantity for o in orders)
            depth.append((price, total_qty))
            count += 1
            if count >= levels:
                break
        return depth