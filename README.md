# Matching Engine Starter (Python)

This is a minimal starter repo for a crypto matching engine prototype using:
- FastAPI (HTTP + WebSocket)
- SortedDict for orderbook price levels
- asyncio-friendly WebSocket broadcast manager

Run:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.api:app --reload --port 8000
```

Endpoints:
- POST /orders  -> submit orders (JSON)
- WebSocket /ws -> subscribe to BBO and trade messages

This is a prototype intended for learning and unit tests. Extend for persistence, concurrency, and performance tuning.
