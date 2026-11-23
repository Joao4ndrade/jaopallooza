import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import DB
from app.models import PasswordResetToken, User
from app.names import normalize_name
from app.schemas import (
    ForgotPasswordIn,
    LoginIn,
    MessageOut,
    NameAvailabilityOut,
    PasswordResetIn,
    RegisterIn,
    TokenOut,
    validate_name,
)
from app.security import (
    create_access_token,
    hash_password,
    hash_reset_token,
    new_reset_token,
    verify_password,
)
from app.services import mailer

router = APIRouter(prefix="/auth", tags=["auth"])

_NAME_TAKEN = "Esse nome já está em uso. Que tal adicionar a inicial do sobrenome?"
_EMAIL_TAKEN = "Esse e-mail já tem conta. Esqueceu a senha?"
_FORGOT_REPLY = (
    "Se esse e-mail estiver cadastrado, enviamos um link para criar uma nova senha. "
    "Confere também a caixa de spam!"
)
_RESEND_COOLDOWN = timedelta(seconds=60)


def _authenticate(db: Session, login: str, password: str) -> User:
    login = login.strip()
    if "@" in login:
        stmt = select(User).where(User.email == login.lower())
    else:
        stmt = select(User).where(User.name_key == normalize_name(login))
    user = db.scalar(stmt)
    if not verify_password(user.password_hash if user else None, password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nome/e-mail ou senha incorretos.")
    return user


def _name_taken(db: Session, name: str) -> bool:
    return bool(db.scalar(select(exists().where(User.name_key == normalize_name(name)))))


@router.get("/name-available", summary="Checa se o nome está livre (usado no cadastro)")
def name_available(db: DB, name: Annotated[str, Query(max_length=60)]) -> NameAvailabilityOut:
    try:
        cleaned = validate_name(name)
    except ValueError as exc:
        return NameAvailabilityOut(available=False, message=str(exc))
    if _name_taken(db, cleaned):
        return NameAvailabilityOut(available=False, message=_NAME_TAKEN)
    return NameAvailabilityOut(available=True, message="Nome disponível!")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: DB) -> TokenOut:
    expected = get_settings().invite_code.strip().casefold()
    provided = (data.invite_code or "").strip().casefold()
    if expected and not secrets.compare_digest(expected, provided):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Código de convite inválido.")

    if _name_taken(db, data.name):
        raise HTTPException(status.HTTP_409_CONFLICT, _NAME_TAKEN)
    if db.scalar(select(exists().where(User.email == data.email))):
        raise HTTPException(status.HTTP_409_CONFLICT, _EMAIL_TAKEN)

    user = User(
        name=data.name,
        name_key=normalize_name(data.name),
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # dois cadastros iguais ao mesmo tempo
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Nome ou e-mail já em uso.") from exc
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login")
def login(data: LoginIn, db: DB) -> TokenOut:
    user = _authenticate(db, data.login, data.password)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/token", summary="Login via formulário (usado pelo botão Authorize do Swagger)")
def token(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> TokenOut:
    user = _authenticate(db, form.username, form.password)
    return TokenOut(access_token=create_access_token(user.id))


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Envia o link de redefinição de senha por e-mail",
)
def forgot_password(data: ForgotPasswordIn, db: DB, background: BackgroundTasks) -> MessageOut:
    # A resposta é sempre a mesma: não dá para usar isso para descobrir quem tem conta.
    user = db.scalar(select(User).where(User.email == data.email))
    if user is None:
        return MessageOut(detail=_FORGOT_REPLY)

    recently_sent = db.scalar(
        select(
            exists().where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.created_at > func.now() - _RESEND_COOLDOWN,
            )
        )
    )
    if not recently_sent:
        settings = get_settings()
        raw, hashed = new_reset_token()
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.password_reset_minutes)
        db.add(PasswordResetToken(user_id=user.id, token_hash=hashed, expires_at=expires_at))
        db.commit()
        link = f"{settings.frontend_url.rstrip('/')}/redefinir-senha?token={raw}"
        # Envia depois de responder: a request não fica esperando o SMTP.
        background.add_task(
            mailer.send_password_reset,
            user.email,
            user.name,
            link,
            settings.password_reset_minutes,
        )
    return MessageOut(detail=_FORGOT_REPLY)


@router.post("/reset-password", summary="Cria a nova senha a partir do link do e-mail")
def reset_password(data: PasswordResetIn, db: DB) -> TokenOut:
    now = datetime.now(UTC)
    reset = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_reset_token(data.token)
        )
    )
    if reset is None or reset.used_at is not None or reset.expires_at <= now:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Esse link é inválido ou expirou. Peça um novo."
        )

    user = db.get(User, reset.user_id)
    user.password_hash = hash_password(data.password)
    user.password_changed_at = now  # desloga os outros aparelhos
    # Este link e qualquer outro pendente da mesma pessoa deixam de valer.
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.commit()
    return TokenOut(access_token=create_access_token(user.id))
