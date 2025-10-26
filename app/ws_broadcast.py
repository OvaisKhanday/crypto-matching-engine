from fastapi import WebSocket
import asyncio

class BroadcastManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.connections.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self.connections.discard(ws)
            try:
                await ws.close()
            except:
                pass

    async def broadcast_json(self, message: dict):
        async with self._lock:
            to_remove = []
            for conn in list(self.connections):
                try:
                    await conn.send_json(message)
                except Exception:
                    to_remove.append(conn)
            for r in to_remove:
                self.connections.discard(r)
