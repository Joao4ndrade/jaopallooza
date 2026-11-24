from fastapi import APIRouter
from sqlalchemy import func, select

from app.config import get_settings
from app.deps import DB, CurrentUser
from app.models import EventInfo, Ticket, User
from app.schemas import EventOut, PersonOut

router = APIRouter(prefix="/event", tags=["evento"])


def build_event(db: DB) -> EventOut:
    info = db.get(EventInfo, 1)
    tickets_count = db.scalar(select(func.count()).select_from(Ticket)) or 0
    event = EventOut.model_validate(info)
    event.tickets_count = tickets_count
    event.invite_required = bool(get_settings().invite_code.strip())
    return event


@router.get("")
def read_event(db: DB) -> EventOut:
    return build_event(db)


@router.get("/attendees", summary="Presenças confirmadas (só para quem tem conta)")
def attendees(_: CurrentUser, db: DB) -> list[PersonOut]:
    # Exige login de propósito: o site é público e a lista tem nome e foto da galera.
    stmt = select(User).join(Ticket, Ticket.user_id == User.id).order_by(User.name_key)
    return [PersonOut.model_validate(u) for u in db.scalars(stmt)]
