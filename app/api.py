from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from decimal import Decimal, getcontext
from pydantic import BaseModel
from app.core.order_types import Order, Side, OrderType
from app.core.order_book import OrderBook
from app.core.matching import match_order
from app.ws_broadcast import BroadcastManager
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger("matching_engine.matching")

# set decimal precision
getcontext().prec = 18

router = APIRouter()
books: Dict[str, OrderBook] = {} # Stores all books, each for individual symbol
trade_broadcast = BroadcastManager() # Broadcast only successful trades
market_data_broadcast = BroadcastManager() # Broadcast BBO and depths of different Symbols

class OrderIn(BaseModel):
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None

@router.get('/')
async def testing_route():
    return {"hello":"world"}

@router.post("/orders") # Route for handling orders
async def submit_order(o: OrderIn):
    # simple validation
    if o.order_type == OrderType.LIMIT and o.price is None:
        raise HTTPException(status_code=400, detail="Limit orders require price")
    if o.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")
    book = books.setdefault(o.symbol, OrderBook(o.symbol))
    order = Order(symbol=o.symbol, side=o.side, order_type=o.order_type, quantity=o.quantity, price=o.price)

    # handle FOK pre-check
    if o.order_type == OrderType.FOK:
        total_avail = Decimal(0)
        if order.side == Side.BUY:
            for price, lvl in list(book.asks.items()):
                if price <= order.price:
                    total_avail += lvl.total_qty
                else:
                    break
        else:
            for price, lvl in reversed(list(book.bids.items())):
                if price >= order.price:
                    total_avail += lvl.total_qty
                else:
                    break
        if total_avail < order.quantity:
            logger.info(f"FOK order killed: {o}")
            return {"status": "killed", "reason": "FOK not fillable"}

    trades = match_order(order, book)
    # publish trades
    for t in trades:
        await trade_broadcast.broadcast_json({**t.__dict__})

    # broadcast order book depth
    [asks, bids] = book.top_n(10)
    asks_bids_depth_of_book = {
        "type": "depth",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "symbol": book.symbol,
        "bids": bids,
        "asks": asks,
    }
    await market_data_broadcast.broadcast_json(asks_bids_depth_of_book)

    # broadcast current BBO
    best_bid, best_ask = book.get_bbo()
    bbo_of_book = {
        "type": "bbo",
        "symbol": book.symbol,
        "best_bid": str(best_bid) if best_bid else None,
        "best_ask": str(best_ask) if best_ask else None
    }
    await market_data_broadcast.broadcast_json(bbo_of_book)

    return {"status": "ok", "trades": [t.__dict__ for t in trades]}

# Subscribe for trade events
@router.websocket("/ws/trades")
async def websocket_endpoint(ws: WebSocket):
    await trade_broadcast.connect(ws)
    try:
        while True:
            msg = await ws.receive_text()
            # echo or ignore client messages; clients receive broadcasts
            await ws.send_json({"message": "ok"})
    except WebSocketDisconnect:
        await trade_broadcast.disconnect(ws)
    except Exception:
        pass
    finally:
        trade_broadcast.disconnect(ws)

# Subscribe for BBO and Symbol depth levels
@router.websocket("/ws/market")
async def market_data_ws(ws: WebSocket):
    """
    Market Data Dissemination API (e.g., WebSocket) to stream real-time market data from the engine. This feed includes:
        - Current BBO (Best Bid & Offer).
        - Order book depth (e.g., top 10 levels of bids and asks).
    """
    await market_data_broadcast.connect(ws)
    try:
        while True:
            msg = await ws.receive_text()
            # echo or ignore client messages; clients receive broadcasts
            await ws.send_json({"message": "ok"})
    except WebSocketDisconnect:
        await market_data_broadcast.disconnect(ws)
    except Exception:
        pass
    finally:
        market_data_broadcast.disconnect(ws)