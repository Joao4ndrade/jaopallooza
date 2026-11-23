import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import DB
from app.models import User
from app.names import normalize_name
from app.schemas import LoginIn, RegisterIn, TokenOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_NAME_TAKEN = "Esse nome já está em uso. Que tal adicionar a inicial do sobrenome?"


def _authenticate(db: Session, name: str, password: str) -> User:
    user = db.scalar(select(User).where(User.name_key == normalize_name(name)))
    if not verify_password(user.password_hash if user else None, password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nome ou senha incorretos.")
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: DB) -> TokenOut:
    expected = get_settings().invite_code.strip().casefold()
    provided = (data.invite_code or "").strip().casefold()
    if expected and not secrets.compare_digest(expected, provided):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Código de convite inválido.")

    name_key = normalize_name(data.name)
    if db.scalar(select(User.id).where(User.name_key == name_key)):
        raise HTTPException(status.HTTP_409_CONFLICT, _NAME_TAKEN)

    user = User(name=data.name, name_key=name_key, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, _NAME_TAKEN) from exc
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login")
def login(data: LoginIn, db: DB) -> TokenOut:
    user = _authenticate(db, data.name, data.password)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/token", summary="Login via formulário (usado pelo botão Authorize do Swagger)")
def token(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> TokenOut:
    user = _authenticate(db, form.username, form.password)
    return TokenOut(access_token=create_access_token(user.id))
