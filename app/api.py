from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from decimal import Decimal, getcontext
from pydantic import BaseModel
from app.core.order_types import Order, Side, OrderType
from app.core.order_book import OrderBook
from app.core.matching import match_order, Trade
from app.ws_broadcast import BroadcastManager
from typing import Dict
from datetime import datetime
import asyncio

# set decimal precision
getcontext().prec = 18

# app = FastAPI(title="Matching Engine Prototype")
router = APIRouter()
books: Dict[str, OrderBook] = {}
broadcast = BroadcastManager()

class OrderIn(BaseModel):
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None

@router.get('/')
async def testing():
    print('GET /')
    return {"hello":"world"}

@router.post("/orders")
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
            return {"status": "killed", "reason": "FOK not fillable"}

    trades = match_order(order, book)
    # publish trades and BBO
    for t in trades:
        await broadcast.broadcast_json({"type": "trade", **t.__dict__})

    best_bid, best_ask = book.get_bbo()
    bbo = {"type": "bbo", "symbol": o.symbol, "best_bid": str(best_bid) if best_bid else None, "best_ask": str(best_ask) if best_ask else None}
    await broadcast.broadcast_json(bbo)
    return {"status": "ok", "trades": [t.__dict__ for t in trades]}

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await broadcast.connect(ws)
    try:
        while True:
            msg = await ws.receive_text()
            # echo or ignore client messages; clients receive broadcasts
            await ws.send_json({"message": "ok"})
    except WebSocketDisconnect:
        await broadcast.disconnect(ws)

active_market_sockets = set()
@router.websocket("/ws/market")
async def market_data_ws(ws: WebSocket):
    await ws.accept()
    active_market_sockets.add(ws)
    await ws.send_text("You are Connected to Market Feed")
    try:
        while True:
            # Prepare market data snapshot
            for book in books.values():
                [asks, bids] = book.top_n(10)
                snapshot = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "symbol": book.symbol,
                    "bids": bids,
                    "asks": asks,
                }
                await ws.send_json(snapshot)
            await asyncio.sleep(1)  # Update every second
    except Exception:
        pass
    finally:
        active_market_sockets.remove(ws)