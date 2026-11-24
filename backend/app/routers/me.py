import secrets

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.deps import DB, CurrentUser, is_admin
from app.models import Ticket, User, UserPhoto
from app.schemas import AwardsParticipationIn, EmailUpdateIn, MeOut, PartnerIn, PersonOut
from app.services import awards, photos

router = APIRouter(prefix="/me", tags=["conta"])


def build_me(db: Session, user: User) -> MeOut:
    partner = db.get(User, user.partner_id) if user.partner_id else None
    if partner is None:
        partner_status = "none"
    elif partner.partner_id == user.id:
        partner_status = "confirmed"
    else:
        partner_status = "pending"

    # "Pedidos" = quem me marcou como par e eu ainda não marquei de volta.
    conditions = [User.partner_id == user.id]
    if user.partner_id is not None:
        conditions.append(User.id != user.partner_id)
    requests_stmt = select(User).where(*conditions).order_by(User.name_key)

    return MeOut(
        id=user.id,
        name=user.name,
        email=user.email,
        photo_url=user.photo_url,
        is_admin=is_admin(user),
        has_ticket=awards.has_ticket(db, user.id),
        awards_opt_in=user.awards_opt_in,
        created_at=user.created_at,
        partner=PersonOut.model_validate(partner) if partner else None,
        partner_status=partner_status,
        partner_requests=[PersonOut.model_validate(u) for u in db.scalars(requests_stmt)],
        competing_in=awards.competing_categories(db, user),
    )


@router.get("")
def read_me(user: CurrentUser, db: DB) -> MeOut:
    return build_me(db, user)


@router.put("/email", summary="Cadastrar ou trocar o e-mail de recuperação")
def set_email(data: EmailUpdateIn, user: CurrentUser, db: DB) -> MeOut:
    taken = db.scalar(select(User.id).where(User.email == data.email, User.id != user.id))
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse e-mail já está em outra conta.")
    user.email = data.email
    db.commit()
    return build_me(db, user)


@router.put("/photo", summary="Enviar ou trocar a foto de perfil")
def upload_photo(file: UploadFile, user: CurrentUser, db: DB) -> MeOut:
    raw = file.file.read(photos.MAX_UPLOAD_BYTES + 1)
    if len(raw) > photos.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, "Foto grande demais (máximo de 8 MB)."
        )
    try:
        data = photos.process_photo(raw)
    except photos.InvalidImage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    record = db.get(UserPhoto, user.id)
    if record is None:
        db.add(UserPhoto(user_id=user.id, data=data, content_type=photos.CONTENT_TYPE))
    else:
        record.data = data
        record.content_type = photos.CONTENT_TYPE
    user.photo_key = secrets.token_urlsafe(16)  # endereço novo: o cache antigo não atrapalha
    db.commit()
    return build_me(db, user)


@router.delete("/photo", summary="Remover a foto de perfil")
def delete_photo(user: CurrentUser, db: DB) -> MeOut:
    db.execute(delete(UserPhoto).where(UserPhoto.user_id == user.id))
    user.photo_key = None
    db.commit()
    return build_me(db, user)


@router.put("/awards", summary="Entrar/sair da votação (como indicado)")
def set_awards_participation(data: AwardsParticipationIn, user: CurrentUser, db: DB) -> MeOut:
    if user.awards_opt_in and not data.opt_in:
        awards.discard_votes_received(db, user)
    user.awards_opt_in = data.opt_in
    db.commit()
    return build_me(db, user)


@router.get("/partner-options", summary="Quem pode ser escolhido como par")
def partner_options(user: CurrentUser, db: DB) -> list[PersonOut]:
    stmt = (
        select(User)
        .join(Ticket, Ticket.user_id == User.id)
        .where(User.id != user.id)
        .order_by(User.name_key)
    )
    return [PersonOut.model_validate(u) for u in db.scalars(stmt)]


@router.put("/partner", summary="Escolher (ou remover) meu par")
def set_partner(data: PartnerIn, user: CurrentUser, db: DB) -> MeOut:
    awards.set_partner(db, user, data.partner_id)
    return build_me(db, user)


@router.delete(
    "", status_code=status.HTTP_204_NO_CONTENT, summary="Cancelar presença e excluir conta"
)
def delete_me(user: CurrentUser, db: DB) -> None:
    # Ingresso, votos, casal e votos recebidos caem juntos via ON DELETE CASCADE;
    # quem tinha essa pessoa como par fica sem par (ON DELETE SET NULL).
    db.execute(delete(User).where(User.id == user.id))
    db.commit()
