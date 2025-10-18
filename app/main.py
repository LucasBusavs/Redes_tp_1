from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect, status
from app.db import engine, Base
from app.routers import auth, users, rooms, messages
from fastapi.openapi.utils import get_openapi
from app.db import get_db
from app.auth_utils import get_current_user, verify_token
from app import models
from sqlalchemy.orm import Session
from app.connection_manager import manager
from app.dm_connection_manager import dm_manager

app = FastAPI(title="Chat API", version="1.0")

# Cria as tabelas no banco (somente para protótipo)
Base.metadata.create_all(bind=engine)

# MARK: - Rotas REST
# app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)


# MARK: - Room WS

@app.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    db: Session = Depends(get_db)
):
    token = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    token = token.split(" ")[1]
    current_user = verify_token(token=token, db=db)
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        await websocket.close(code=1008)  # Policy Violation
        return

    user_in_room = db.query(models.UserRoom).filter_by(
        user_id=current_user.id, room_id=room_id
    ).first()
    if not user_in_room:
        await websocket.close(code=1008)
        return

    await manager.connect(room_id, websocket)

    try:
        # Mantém a conexão aberta (sem tratar mensagens)
        while True:
            await websocket.receive_text()  # só mantém a conexão viva
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)


# MARK: - DM WS

@app.websocket("/ws/dm")
async def dm_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    token = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    token = token.split(" ")[1]
    current_user = verify_token(token=token, db=db)
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Registra o WebSocket do remetente
    await dm_manager.connect(current_user.id, websocket)

    try:
        while True:
            # Recebe mensagem do remetente
            await websocket.receive_text()
    except WebSocketDisconnect:
        dm_manager.disconnect(current_user.id, websocket)

#MARK: - OpenAPI

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema.setdefault(
        "components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi()
