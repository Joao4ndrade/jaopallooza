import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings

_hasher = PasswordHasher()
# Usado quando o nome não existe, para o login demorar o mesmo tanto (evita descobrir nomes).
_DUMMY_HASH = _hasher.hash("jaopallooza-dummy-password")
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_expires_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


@dataclass(frozen=True)
class AccessToken:
    user_id: uuid.UUID
    issued_at: int  # segundos desde a época (UTC)


def decode_access_token(token: str) -> AccessToken | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGORITHM])
        return AccessToken(user_id=uuid.UUID(payload["sub"]), issued_at=int(payload["iat"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def token_predates(token: AccessToken, moment: datetime | None) -> bool:
    """True se o token foi emitido antes de `moment` (ex.: antes da última troca de senha)."""
    return moment is not None and token.issued_at < int(moment.timestamp())


def new_reset_token() -> tuple[str, str]:
    """Gera (token para o link, hash para o banco)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
