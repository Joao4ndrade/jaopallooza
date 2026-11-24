import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import CategoryKind
from app.names import NAME_PATTERN, clean_name


def validate_name(value: str) -> str:
    value = clean_name(value)
    if len(value) < 2:
        raise ValueError("O nome precisa ter pelo menos 2 letras.")
    if len(value) > 30:
        raise ValueError("O nome pode ter no máximo 30 caracteres.")
    if not NAME_PATTERN.match(value):
        raise ValueError("Use só letras, números, espaço, ponto, hífen ou apóstrofo.")
    return value


def _lower(value: str) -> str:
    return value.strip().lower()


# ---------- auth ----------


class RegisterIn(BaseModel):
    name: str = Field(max_length=60, examples=["João"])
    email: EmailStr = Field(examples=["joao@exemplo.com"])
    password: str = Field(min_length=6, max_length=128)
    invite_code: str | None = None

    _name = field_validator("name")(validate_name)
    _email = field_validator("email")(_lower)


class LoginIn(BaseModel):
    # Nome ou e-mail
    login: str = Field(max_length=254, examples=["João"])
    password: str = Field(max_length=128)


class NameAvailabilityOut(BaseModel):
    available: bool
    message: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr

    _email = field_validator("email")(_lower)


class PasswordResetIn(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(min_length=6, max_length=128)


class MessageOut(BaseModel):
    detail: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- conta ----------


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    photo_url: str | None = None


class CategoryRef(BaseModel):
    id: int
    title: str
    emoji: str


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    photo_url: str | None
    is_admin: bool
    has_ticket: bool
    awards_opt_in: bool
    created_at: datetime
    partner: PersonOut | None
    partner_status: Literal["none", "pending", "confirmed"]
    # Pessoas que marcaram você como par e ainda não foram confirmadas por você.
    partner_requests: list[PersonOut]
    competing_in: list[CategoryRef]


class AwardsParticipationIn(BaseModel):
    opt_in: bool


class EmailUpdateIn(BaseModel):
    email: EmailStr

    _email = field_validator("email")(_lower)


class PartnerIn(BaseModel):
    partner_id: uuid.UUID | None


# ---------- evento / ingresso ----------


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    tagline: str | None
    description: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    venue_name: str | None
    venue_address: str | None
    city: str | None
    maps_url: str | None
    tickets_count: int = 0
    invite_required: bool = False


class TicketOut(BaseModel):
    code: str
    holder_name: str
    created_at: datetime
    checked_in_at: datetime | None


# ---------- awards ----------


class MemberOut(BaseModel):
    name: str
    photo_url: str | None


class NomineeOut(BaseModel):
    # Para categorias individuais é o id da pessoa; para "casal", o id do casal.
    id: uuid.UUID
    name: str
    members: list[MemberOut]


class MyVoteOut(BaseModel):
    nominee: NomineeOut
    voted_at: datetime


class CategoryOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    emoji: str
    kind: CategoryKind
    nominees: list[NomineeOut]
    my_vote: MyVoteOut | None
    i_am_nominee: bool


class AwardsOut(BaseModel):
    can_vote: bool
    categories: list[CategoryOut]


class VoteIn(BaseModel):
    nominee_id: uuid.UUID


# ---------- admin ----------


class EventUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    tagline: str | None = Field(default=None, max_length=160)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    venue_name: str | None = Field(default=None, max_length=120)
    venue_address: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=80)
    maps_url: str | None = Field(default=None, max_length=500)


class CategoryIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{2,60}$", examples=["mais-provavel-de-sumir"])
    title: str = Field(max_length=80, examples=["Mais provável de sumir sem avisar"])
    description: str | None = Field(default=None, max_length=240)
    emoji: str = Field(default="🏆", max_length=16)
    kind: CategoryKind = CategoryKind.INDIVIDUAL
    position: int = 0


class CategoryUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=240)
    emoji: str | None = Field(default=None, max_length=16)
    position: int | None = None
    is_active: bool | None = None


class CategoryAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str | None
    emoji: str
    kind: CategoryKind
    position: int
    is_active: bool


class RankingEntry(BaseModel):
    name: str
    votes: int


class CategoryResultOut(BaseModel):
    id: int
    title: str
    emoji: str
    total_votes: int
    ranking: list[RankingEntry]


class GuestOut(BaseModel):
    id: uuid.UUID
    name: str
    ticket_code: str
    ticket_created_at: datetime
    checked_in_at: datetime | None


class AdminResetPasswordIn(BaseModel):
    name: str
    new_password: str = Field(min_length=6, max_length=128)
