from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from app.db import get_db
from app.auth_utils import get_current_user
import asyncio
from datetime import datetime
from app.connection_manager import manager

router = APIRouter(prefix="/rooms", tags=["Rooms"])

# MARK: - Create
@router.post("/", response_model=schemas.Room)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_room = models.Room(name=room.name, owner_id=current_user.id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    # adiciona automaticamente o criador à sala
    user_room = models.UserRoom(user_id=current_user.id, room_id=db_room.id)
    db.add(user_room)
    db.commit()

    return db_room

# MARK: - Delete
@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode excluir a sala")

    db.delete(room)
    db.commit()
    return {"message": "Sala removida com sucesso"}


# MARK: - Enter
@router.post("/{room_id}/enter")
def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    already_in_room = db.query(models.UserRoom).filter_by(
        user_id=current_user.id, room_id=room_id
    ).first()
    if already_in_room:
        raise HTTPException(status_code=400, detail="Você já está na sala")

    db.add(models.UserRoom(user_id=current_user.id, room_id=room_id))
    db.commit()
    return {"message": f"Usuário {current_user.username} entrou na sala {room.name}"}

# MARK: - Leave
@router.delete("/{room_id}/leave")
def leave_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    relation = db.query(models.UserRoom).filter_by(
        user_id=current_user.id, room_id=room_id
    ).first()
    if not relation:
        raise HTTPException(status_code=400, detail="Você não está nessa sala")
    
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="O dono não pode sair da sala")

    db.delete(relation)
    db.commit()
    return {"message": f"{current_user.username} saiu da sala {room.name}"}

# MARK: - Remove user
@router.delete("/{room_id}/users/{user_id}")
def remove_user_from_room(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode remover usuários")
    
    if room.owner_id == user_id:
        raise HTTPException(
            status_code=400, detail="O dono da sala não pode ser removido")
    
    relation = db.query(models.UserRoom).filter_by(
        user_id=user_id, room_id=room_id
    ).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Usuário não está na sala")

    db.delete(relation)
    db.commit()
    return {"message": f"Usuário removido da sala {room.name}"}

# MARK: - Send messages

def _user_in_room(room: models.Room, user_id: int) -> bool:
    # tenta usar relação room.users (mais comum). Ajuste se seu modelo for outro.
    try:
        users = getattr(room, "users", None)
        if users is None:
            return False
        return any(u.id == user_id for u in users)
    except Exception:
        return False


@router.post("/{room_id}/messages")
async def send_message(
    room_id: int,
    msg: schemas.MessageCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
    ):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    if not _user_in_room(room, current_user.id):
        raise HTTPException(
            status_code=403, detail="Você não faz parte desta sala")

    message = models.Message(
        room_id=room.id,
        user_id=current_user.id,
        content=msg.content,
        timestamp=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    
    await asyncio.create_task(manager.broadcast(room_id, message=message))

    return message

# MARK: - Get messages

@router.get("/{room_id}/messages")
def get_messages(room_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    if not _user_in_room(room, current_user.id):
        raise HTTPException(
            status_code=403, detail="Você não tem acesso a esta sala")

    messages = db.query(models.Message).filter(
        models.Message.room_id == room_id).all()
    return messages

# MARK: - Get all rooms
@router.get("/", response_model=list[schemas.Room])
def list_rooms(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Room).options(joinedload(models.Room.users)).all()
