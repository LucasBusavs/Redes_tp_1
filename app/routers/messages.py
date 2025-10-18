from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db import get_db
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from datetime import datetime


SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"


router = APIRouter(prefix="/messages", tags=["Messages"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(
        models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def _user_in_room(room: models.Room, user_id: int) -> bool:
    # tenta usar relação room.users (mais comum). Ajuste se seu modelo for outro.
    try:
        users = getattr(room, "users", None)
        if users is None:
            return False
        return any(u.id == user_id for u in users)
    except Exception:
        return False


@router.post("/")
def send_message(msg: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    room = db.query(models.Room).filter(models.Room.id == msg.room_id).first()
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
    return message


@router.post("/direct/{receiver_id}")
def send_direct_message(
    receiver_id: int,
    msg: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    receiver = db.query(models.User).filter(
        models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=404, detail="Usuário de destino não encontrado")

    direct_msg = models.DirectMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=msg.content
    )
    db.add(direct_msg)
    db.commit()
    db.refresh(direct_msg)
    return {"message": "Mensagem direta enviada com sucesso"}


@router.get("/{room_id}")
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
