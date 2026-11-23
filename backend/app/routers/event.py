from fastapi import APIRouter
from sqlalchemy import func, select

from app.config import get_settings
from app.deps import DB
from app.models import EventInfo, Ticket
from app.schemas import EventOut

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
