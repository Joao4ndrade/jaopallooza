"""Endpoints da organização. Por enquanto o "painel" é o Swagger em /api/docs."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, get_admin
from app.models import AwardCategory, CategoryKind, EventInfo, Ticket, User, Vote
from app.names import normalize_name
from app.routers.event import build_event
from app.schemas import (
    CategoryAdminOut,
    CategoryIn,
    CategoryResultOut,
    CategoryUpdateIn,
    EventOut,
    EventUpdateIn,
    GuestOut,
    RankingEntry,
    ResetPasswordIn,
    TicketOut,
)
from app.security import hash_password
from app.services import awards

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin)])


@router.get("/guests", summary="Lista de confirmados")
def list_guests(db: DB) -> list[GuestOut]:
    stmt = select(User, Ticket).join(Ticket, Ticket.user_id == User.id).order_by(User.name_key)
    return [
        GuestOut(
            id=user.id,
            name=user.name,
            ticket_code=ticket.code,
            ticket_created_at=ticket.created_at,
            checked_in_at=ticket.checked_in_at,
        )
        for user, ticket in db.execute(stmt).all()
    ]


@router.get("/results", summary="Resultado do Awards (segredo até a festa!)")
def results(db: DB) -> list[CategoryResultOut]:
    names = {u.id: u.name for u in db.scalars(select(User))}
    couples = {c.couple.id: c.to_out().name for c in awards.couple_nominees(db)}
    out = []
    for category in awards.active_categories(db):
        if category.kind == CategoryKind.COUPLE:
            column, labels = Vote.nominee_couple_id, couples
        else:
            column, labels = Vote.nominee_user_id, names
        stmt = (
            select(column, func.count())
            .where(Vote.category_id == category.id)
            .group_by(column)
            .order_by(func.count().desc())
        )
        ranking = [
            RankingEntry(name=labels.get(nominee_id, "?"), votes=count)
            for nominee_id, count in db.execute(stmt).all()
        ]
        out.append(
            CategoryResultOut(
                id=category.id,
                title=category.title,
                emoji=category.emoji,
                total_votes=sum(r.votes for r in ranking),
                ranking=ranking,
            )
        )
    return out


@router.put("/event", summary="Atualizar dados do evento")
def update_event(data: EventUpdateIn, db: DB) -> EventOut:
    info = db.get(EventInfo, 1)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(info, field, value)
    db.commit()
    return build_event(db)


@router.get("/categories")
def list_all_categories(db: DB) -> list[CategoryAdminOut]:
    stmt = select(AwardCategory).order_by(AwardCategory.position, AwardCategory.id)
    return [CategoryAdminOut.model_validate(c) for c in db.scalars(stmt)]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryIn, db: DB) -> CategoryAdminOut:
    category = AwardCategory(**data.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe categoria com esse slug.") from exc
    return CategoryAdminOut.model_validate(category)


@router.patch("/categories/{category_id}")
def update_category(category_id: int, data: CategoryUpdateIn, db: DB) -> CategoryAdminOut:
    category = db.get(AwardCategory, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    return CategoryAdminOut.model_validate(category)


def _ticket_by_code(db: DB, code: str) -> tuple[Ticket, User]:
    row = db.execute(
        select(Ticket, User)
        .join(User, User.id == Ticket.user_id)
        .where(Ticket.code == code.strip().upper())
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ingresso não encontrado.")
    return row[0], row[1]


@router.get("/tickets/{code}", summary="Consultar ingresso pelo código do QR")
def get_ticket(code: str, db: DB) -> TicketOut:
    ticket, user = _ticket_by_code(db, code)
    return TicketOut(
        code=ticket.code,
        holder_name=user.name,
        created_at=ticket.created_at,
        checked_in_at=ticket.checked_in_at,
    )


@router.post("/tickets/{code}/check-in", summary="Fazer check-in na portaria")
def check_in(code: str, db: DB) -> TicketOut:
    ticket, user = _ticket_by_code(db, code)
    if ticket.checked_in_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{user.name} já fez check-in.")
    ticket.checked_in_at = datetime.now(UTC)
    db.commit()
    return TicketOut(
        code=ticket.code,
        holder_name=user.name,
        created_at=ticket.created_at,
        checked_in_at=ticket.checked_in_at,
    )


@router.post("/users/reset-password", summary="Redefinir senha de alguém que esqueceu")
def reset_password(data: ResetPasswordIn, db: DB) -> dict[str, str]:
    user = db.scalar(select(User).where(User.name_key == normalize_name(data.name)))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ninguém com esse nome.")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"detail": f"Senha de {user.name} redefinida."}
