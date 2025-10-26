from decimal import Decimal
from typing import List
from app.core.order_book import OrderBook
from app.core.order_types import Order, Side, OrderType
from dataclasses import dataclass
from datetime import datetime
import uuid
import logging

logger = logging.getLogger("matching_engine.matching")

@dataclass
class Trade:
    trade_id: str
    timestamp: str
    symbol: str
    price: str
    quantity: str
    aggressor_side: str
    maker_order_id: str
    taker_order_id: str

def _emit_trade(symbol, price: Decimal, qty: Decimal, aggressor: Side, maker_id: str, taker_id: str) -> Trade:
    return Trade(
        trade_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
        symbol=symbol,
        price=str(price),
        quantity=str(qty),
        aggressor_side=aggressor.value,
        maker_order_id=maker_id,
        taker_order_id=taker_id
    )

def match_order(order: Order, ob: OrderBook) -> List[Trade]:
    logger.info(f"🔄 Matching order: {order}")
    trades: List[Trade] = []
    remaining = order.quantity

    if order.side == Side.BUY:
        opposing = ob.asks
        # iterate ascending
        price_items = list(opposing.items())
    else:
        opposing = ob.bids
        price_items = list(opposing.items())

    def price_ok(price: Decimal) -> bool:
        if order.order_type == OrderType.MARKET:
            return True
        if order.side == Side.BUY:
            return price <= order.price
        else:
            return price >= order.price

    for price, level in price_items:
        if remaining <= 0:
            break
        if not price_ok(price):
            break
        while level.orders and remaining > 0:
            maker = level.orders[0]
            match_qty = min(remaining, maker.quantity)
            trades.append(_emit_trade(order.symbol, price, match_qty, order.side, maker.id, order.id))
            maker.quantity -= match_qty
            level.total_qty -= match_qty
            remaining -= match_qty
            if maker.quantity == 0:
                level.orders.popleft()
        if level.total_qty == 0:
            try:
                del opposing[price]
            except KeyError:
                pass

    # rest on book if limit and remaining
    if remaining > 0 and order.order_type == OrderType.LIMIT:
        rest_order = Order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=remaining,
            price=order.price,
            timestamp=order.timestamp,
            id=order.id
        )
        ob.add_limit_order(rest_order)

    if len(trades) > 0:
        logger.info(f"✅ Trade successful: {trades}")

    return trades
