# Matching Engine

## Introduction

This is a high-performance cryptocurrency matching engine. This engine implements core trading functionalities based on REG NMS-inspired principles of price-time priority and internal order protection. Additionally, the engine generates its own stream of trade execution data.

![Matching Engine Demo](./static/demo.gif)

- FastAPI (HTTP + WebSocket)
- SortedDict for orderbook price levels
- asyncio-friendly WebSocket broadcast manager

Run:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app
```

Run tests:

```bash
python -m pytest -v
```

Endpoints:

- POST `/orders` -> Submit orders

```json
{
 "symbol":"BTC-USDT",
 "side":"sell" | "buy",
 "order_type":"market" | "limit" | "ioc" | "fok",
 "quantity":10,
 "price": 900
}
```

- WebSocket `/ws/trades` -> successful trade messages
- WebSocket `/ws/market` -> Market Data Dissemination. This feed includes:
  - Current BBO
  - Order book depth (e.g., top 10 levels of bids and asks)

## Sample orders

You can post orders to the server by running `client.js` file. The code generates a series of request with random order types, prices and quantities.

Run

```bash
node client.js
```

## Sample outputs

- POST `/orders`

```json
{
  "status": "ok",
  "trades": [
    {
      "trade_id": "98168ce0-3aef-4eab-b82b-63302e3ded06",
      "timestamp": "2025-10-26T10:28:34.973435Z",
      "symbol": "BTC-USDT",
      "price": "900",
      "quantity": "10",
      "aggressor_side": "sell",
      "maker_order_id": "78b97b91-5018-43c3-a6cd-9e5fa1335118",
      "taker_order_id": "8ad252d2-bd0b-4d2b-819b-89d87404eace"
    }
  ]
}
```

- `/ws/trades`

```json
{
  "trade_id": "1c61dd7c-faf6-461e-8675-ef0d55fd2699",
  "timestamp": "2025-10-26T12:58:02.578019Z",
  "symbol": "BTC-USDT",
  "price": "35034.45",
  "quantity": "181.74",
  "aggressor_side": "sell",
  "maker_order_id": "fd35fd5a-57fd-4e50-8c21-359e500053da",
  "taker_order_id": "7fc7135e-b459-49f3-aa05-0e18b219da81"
}
```

- `/ws/market`

```json
{
    "type":"bbo",
    "symbol":"ETH-USDT",
    "best_bid":"784.26",
    "best_ask":"16020.53"
}

{
  "type": "depth",
  "timestamp": "2025-10-26T13:00:08.481831Z",
  "symbol": "XRP-USDT",
  "bids": [],
  "asks": [
    ["40989.7", "691.67"],
    ["96130.76", "665.03"]
  ]
}
```

## Logging

The logs are consoled and persisted into a file as well `logs/app.log`. We can extend it to store log in multiple files in order to make files easy to handle.
