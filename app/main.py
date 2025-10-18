from fastapi import FastAPI, WebSocket
from app.db import engine, Base
from app.routers import auth, users, rooms, messages

app = FastAPI(title="Chat API", version="1.0")

# Cria as tabelas no banco (somente para protótipo)
Base.metadata.create_all(bind=engine)

# Rotas REST
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)

# WebSocket simples de exemplo


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    await websocket.accept()
    await websocket.send_text(f"Conectado à sala {room_id}!")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Você disse: {data}")
    except Exception:
        await websocket.close()
