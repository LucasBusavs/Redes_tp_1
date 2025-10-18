from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db import get_db
from datetime import datetime
from app.auth_utils import get_current_user
import asyncio
from app.dm_connection_manager import dm_manager


router = APIRouter(prefix="/messages", tags=["Messages"])



# MARK: - Send Direct message

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

    asyncio.create_task(dm_manager.send_direct_message(receiver_id, message=direct_msg))

    return {"message": "Mensagem direta enviada com sucesso"}

# MARK: - Get Direct messages

@router.get("/direct/{receiver_id}")
def get_direct_messages(
    receiver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    messages = db.query(models.DirectMessage).filter_by(
        sender_id=current_user.id, receiver_id=receiver_id
    ).all()

    return messages
