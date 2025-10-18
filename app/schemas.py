from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# ============================================================
# Usuário
# ============================================================


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# ============================================================
# Sala
# ============================================================

class RoomBase(BaseModel):
    name: str


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: int
    owner_id: int
    users: Optional[List[User]] = []

    class Config:
        from_attributes = True


# ============================================================
# Mensagem (em sala)
# ============================================================

class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    user_id: int
    room_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================================
# Mensagem direta (DM)
# ============================================================

class DirectMessageBase(BaseModel):
    content: str


class DirectMessageCreate(DirectMessageBase):
    pass


class DirectMessage(DirectMessageBase):
    id: int
    sender_id: int
    receiver_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
