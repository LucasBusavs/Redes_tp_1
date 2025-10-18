from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relações
    rooms = relationship("Room", secondary="user_rooms",
                         back_populates="users")
    messages = relationship("Message", back_populates="user")  # <- importante!


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    # description = Column(String, unique=False, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relações
    users = relationship("User", secondary="user_rooms",
                         back_populates="rooms")
    messages = relationship("Message", back_populates="room")
    owner = relationship("User", backref="owned_rooms")


class UserRoom(Base):
    __tablename__ = "user_rooms"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), primary_key=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    # Relações
    # <- aqui conversa com User.messages
    user = relationship("User", back_populates="messages")
    # <- aqui conversa com Room.messages
    room = relationship("Room", back_populates="messages")


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[
                          sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[
                            receiver_id], backref="received_messages")
