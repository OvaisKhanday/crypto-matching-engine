from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
import uuid
from enum import Enum

class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"
    FOK = "fok"

@dataclass
class Order:
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
