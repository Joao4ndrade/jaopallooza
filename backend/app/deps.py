from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User
from app.security import decode_access_token, token_predates

# tokenUrl aponta para /api/auth/token, o que habilita o botão "Authorize" do Swagger (/api/docs).
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

DB = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str | None, Depends(_oauth2)], db: DB) -> User:
    access = decode_access_token(token) if token else None
    user = db.get(User, access.user_id) if access else None
    if user is None or token_predates(access, user.password_changed_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sua sessão expirou. Entra de novo aí!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def is_admin(user: User) -> bool:
    return user.name_key in get_settings().admin_name_keys


def get_admin(user: CurrentUser) -> User:
    if not is_admin(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Área restrita à organização.")
    return user
