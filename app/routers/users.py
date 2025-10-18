from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, db
# Importa a função que valida o token
from app.auth_utils import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# Dependência do banco
def get_db():
    dataBase = db.SessionLocal()
    try:
        yield dataBase
    finally:
        dataBase.close()


# 🔒 Listar todos os usuários (somente autenticado)
@router.get("/", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    users = db.query(models.User).all()
    return users


# 🔒 Buscar um usuário específico (somente autenticado)
@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
