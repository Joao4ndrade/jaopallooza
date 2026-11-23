import secrets

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import DB, CurrentUser
from app.models import Ticket, User
from app.schemas import TicketOut

router = APIRouter(prefix="/tickets", tags=["ingressos"])

# Sem 0/O, 1/I: fica fácil de ler em voz alta na portaria.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_code() -> str:
    chunk = lambda: "".join(secrets.choice(_ALPHABET) for _ in range(4))  # noqa: E731
    return f"JPZ-{chunk()}-{chunk()}"


def ticket_out(ticket: Ticket, holder: User) -> TicketOut:
    return TicketOut(
        code=ticket.code,
        holder_name=holder.name,
        created_at=ticket.created_at,
        checked_in_at=ticket.checked_in_at,
    )


def find_ticket(db: Session, user: User) -> Ticket | None:
    return db.scalar(select(Ticket).where(Ticket.user_id == user.id))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Garantir ingresso")
def claim_ticket(user: CurrentUser, db: DB, response: Response) -> TicketOut:
    existing = find_ticket(db, user)
    if existing:
        response.status_code = status.HTTP_200_OK
        return ticket_out(existing, user)

    for _ in range(5):
        ticket = Ticket(user_id=user.id, code=generate_code())
        db.add(ticket)
        try:
            db.commit()
            return ticket_out(ticket, user)
        except IntegrityError:
            db.rollback()
            # Ou o código colidiu (raríssimo) ou houve clique duplo: nesse caso já existe.
            existing = find_ticket(db, user)
            if existing:
                response.status_code = status.HTTP_200_OK
                return ticket_out(existing, user)
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Tente de novo em instantes.")


@router.get("/me", summary="Meu ingresso")
def my_ticket(user: CurrentUser, db: DB) -> TicketOut:
    ticket = find_ticket(db, user)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Você ainda não garantiu seu ingresso.")
    return ticket_out(ticket, user)
