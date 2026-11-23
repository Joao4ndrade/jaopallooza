import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CategoryKind(StrEnum):
    INDIVIDUAL = "individual"
    COUPLE = "couple"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(30))
    # Versão normalizada do nome (sem acento/maiúsculas): garante unicidade e é usada no login.
    name_key: Mapped[str] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Sempre em minúsculas. Opcional no banco só para contas antigas; o cadastro exige.
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    # Tokens de login emitidos antes disso deixam de valer (troca de senha desloga tudo).
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # False = a pessoa "saiu da votação": continua votando, mas não concorre.
    awards_opt_in: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    # Par declarado. Vira casal (e concorre a "Melhor casal") só quando é recíproco.
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    """Link de "esqueci minha senha". Guardamos só o hash: o token em si vai no e-mail."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    code: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EventInfo(Base):
    """Linha única com os dados do evento. Campos nulos aparecem como "Em breve" no site."""

    __tablename__ = "event_info"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    tagline: Mapped[str | None] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    venue_name: Mapped[str | None] = mapped_column(String(120))
    venue_address: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(80))
    maps_url: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AwardCategory(Base):
    __tablename__ = "award_categories"
    __table_args__ = (CheckConstraint("kind IN ('individual', 'couple')", name="kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(240))
    emoji: Mapped[str] = mapped_column(String(16), default="🏆", server_default="🏆")
    kind: Mapped[str] = mapped_column(
        String(20), default=CategoryKind.INDIVIDUAL, server_default=CategoryKind.INDIVIDUAL
    )
    position: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))


class Couple(Base):
    """Casal confirmado: os dois se escolheram como par. Par ordenado para não duplicar."""

    __tablename__ = "couples"
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_couples_pair"),
        CheckConstraint("user_a_id < user_b_id", name="ordered_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        # Regra de ouro do Awards: um voto por pessoa por categoria.
        UniqueConstraint("voter_id", "category_id", name="uq_votes_one_per_category"),
        CheckConstraint(
            "(nominee_user_id IS NULL) <> (nominee_couple_id IS NULL)", name="one_nominee"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    voter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("award_categories.id", ondelete="CASCADE"))
    nominee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    nominee_couple_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("couples.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
