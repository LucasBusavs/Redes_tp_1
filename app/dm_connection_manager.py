from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.models import DirectMessage


class DMConnectionManager:
    def __init__(self):
        # user_id -> lista de websockets conectados
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)

    async def send_direct_message(self, user_id: int, message: DirectMessage):
        """Envia mensagem para todos os WebSockets ativos do usuário destinatário"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

dm_manager = DMConnectionManager()