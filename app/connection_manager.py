from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.models import Message

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(websocket)
        await websocket.send_text(f"Conectado à sala {room_id}!")

    def disconnect(self, room_id: int, websocket: WebSocket):
        self.active_connections[room_id].remove(websocket)

    async def broadcast(self, room_id: int, message: Message):
        """Envia JSON para todos na sala"""
        if room_id in self.active_connections:
            message_dict = self.message_to_dict(message=message)
            for connection in self.active_connections[room_id]:
                await connection.send_json(message_dict)

    def message_to_dict(self, message: Message):
        return {
            "id": message.id,
            "content": message.content,
            "user_id": message.user_id,
            "room_id": message.room_id,
            "timestamp": message.timestamp.isoformat()  # datetime -> string
        }

manager = ConnectionManager()