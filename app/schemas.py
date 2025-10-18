from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class RoomCreate(BaseModel):
    name: str


class RoomOut(RoomCreate):
    id: int

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    room_id: int
    content: str


class MessageOut(MessageCreate):
    id: int
    sender_id: int

    class Config:
        orm_mode = True
