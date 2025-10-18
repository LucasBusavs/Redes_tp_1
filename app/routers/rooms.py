from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db import get_db
from app.routers.auth import create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os

router = APIRouter(prefix="/rooms", tags=["Rooms"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"


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


@router.post("/{room_id}/join")
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

    db.delete(relation)
    db.commit()
    return {"message": f"{current_user.username} saiu da sala"}


@router.delete("/{room_id}/remove_user/{user_id}")
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

    relation = db.query(models.UserRoom).filter_by(
        user_id=user_id, room_id=room_id
    ).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Usuário não está na sala")

    db.delete(relation)
    db.commit()
    return {"message": f"Usuário removido da sala {room.name}"}


@router.get("/")
def list_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()
