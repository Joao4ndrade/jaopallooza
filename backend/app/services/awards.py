"""Regras do JAOPALLOOZA Awards.

- Só quem garantiu ingresso vota e concorre.
- Cada pessoa vota uma única vez por categoria e não pode votar em si mesma.
- Categorias "individual": concorre quem tem ingresso e não saiu da votação.
- Categoria "casal": concorre um casal confirmado, ou seja, duas pessoas que se marcaram
  mutuamente como par na aba Conta (e que ambas têm ingresso e não saíram da votação).
- Quando alguém deixa de concorrer (sai da votação, desfaz o casal ou exclui a conta), os
  votos recebidos são descartados e quem votou ganha o voto de volta naquela categoria.
"""

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.models import AwardCategory, CategoryKind, Couple, Ticket, User, Vote
from app.schemas import CategoryOut, CategoryRef, MemberOut, MyVoteOut, NomineeOut


@dataclass(frozen=True)
class CoupleNominee:
    couple: Couple
    first: User
    second: User

    @property
    def member_ids(self) -> set[uuid.UUID]:
        return {self.first.id, self.second.id}

    def to_out(self) -> NomineeOut:
        return NomineeOut(
            id=self.couple.id,
            name=f"{self.first.name} & {self.second.name}",
            members=[_member(self.first), _member(self.second)],
        )


def _member(user: User) -> MemberOut:
    return MemberOut(name=user.name, photo_url=user.photo_url)


def _user_nominee(user: User) -> NomineeOut:
    return NomineeOut(id=user.id, name=user.name, members=[_member(user)])


def _has_ticket_clause(user_id_column):
    return exists().where(Ticket.user_id == user_id_column)


def has_ticket(db: Session, user_id: uuid.UUID) -> bool:
    return bool(db.scalar(select(_has_ticket_clause(user_id))))


def active_categories(db: Session) -> list[AwardCategory]:
    stmt = (
        select(AwardCategory)
        .where(AwardCategory.is_active)
        .order_by(AwardCategory.position, AwardCategory.id)
    )
    return list(db.scalars(stmt))


def individual_nominees(db: Session) -> list[User]:
    stmt = (
        select(User).where(User.awards_opt_in, _has_ticket_clause(User.id)).order_by(User.name_key)
    )
    return list(db.scalars(stmt))


def couple_nominees(db: Session) -> list[CoupleNominee]:
    user_a, user_b = aliased(User), aliased(User)
    stmt = (
        select(Couple, user_a, user_b)
        .join(user_a, Couple.user_a_id == user_a.id)
        .join(user_b, Couple.user_b_id == user_b.id)
        .where(
            user_a.awards_opt_in,
            user_b.awards_opt_in,
            _has_ticket_clause(user_a.id),
            _has_ticket_clause(user_b.id),
        )
    )
    nominees = []
    for couple, a, b in db.execute(stmt).all():
        first, second = sorted((a, b), key=lambda u: u.name_key)
        nominees.append(CoupleNominee(couple, first, second))
    return sorted(nominees, key=lambda n: (n.first.name_key, n.second.name_key))


def couple_of(db: Session, user_id: uuid.UUID) -> Couple | None:
    stmt = select(Couple).where(or_(Couple.user_a_id == user_id, Couple.user_b_id == user_id))
    return db.scalar(stmt)


# ---------- leitura ----------


def _my_vote_out(db: Session, vote: Vote) -> MyVoteOut | None:
    if vote.nominee_user_id:
        user = db.get(User, vote.nominee_user_id)
        nominee = _user_nominee(user) if user else None
    else:
        couple = db.get(Couple, vote.nominee_couple_id)
        nominee = None
        if couple:
            a, b = db.get(User, couple.user_a_id), db.get(User, couple.user_b_id)
            first, second = sorted((a, b), key=lambda u: u.name_key)
            nominee = CoupleNominee(couple, first, second).to_out()
    return MyVoteOut(nominee=nominee, voted_at=vote.created_at) if nominee else None


def build_categories(db: Session, user: User) -> list[CategoryOut]:
    individuals = individual_nominees(db)
    couples = couple_nominees(db)
    my_votes = {v.category_id: v for v in db.scalars(select(Vote).where(Vote.voter_id == user.id))}

    result = []
    for category in active_categories(db):
        if category.kind == CategoryKind.COUPLE:
            options = [c.to_out() for c in couples if user.id not in c.member_ids]
            i_am_nominee = any(user.id in c.member_ids for c in couples)
        else:
            options = [_user_nominee(u) for u in individuals if u.id != user.id]
            i_am_nominee = any(u.id == user.id for u in individuals)

        vote = my_votes.get(category.id)
        result.append(
            CategoryOut(
                id=category.id,
                slug=category.slug,
                title=category.title,
                description=category.description,
                emoji=category.emoji,
                kind=CategoryKind(category.kind),
                nominees=options,
                my_vote=_my_vote_out(db, vote) if vote else None,
                i_am_nominee=i_am_nominee,
            )
        )
    return result


def competing_categories(db: Session, user: User) -> list[CategoryRef]:
    if not user.awards_opt_in or not has_ticket(db, user.id):
        return []
    in_couple = any(user.id in c.member_ids for c in couple_nominees(db))
    return [
        CategoryRef(id=c.id, title=c.title, emoji=c.emoji)
        for c in active_categories(db)
        if c.kind == CategoryKind.INDIVIDUAL or in_couple
    ]


# ---------- escrita ----------


def cast_vote(db: Session, voter: User, category_id: int, nominee_id: uuid.UUID) -> None:
    if not has_ticket(db, voter.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Garanta seu ingresso para votar.")

    category = db.get(AwardCategory, category_id)
    if category is None or not category.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")

    already_voted = db.scalar(
        select(exists().where(Vote.voter_id == voter.id, Vote.category_id == category_id))
    )
    if already_voted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Você já votou nessa categoria.")

    if category.kind == CategoryKind.COUPLE:
        valid = {c.couple.id: c for c in couple_nominees(db)}
        chosen = valid.get(nominee_id)
        if chosen and voter.id in chosen.member_ids:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Votar no próprio casal não vale 😅"
            )
        if chosen is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Casal inválido.")
        vote = Vote(voter_id=voter.id, category_id=category_id, nominee_couple_id=nominee_id)
    else:
        if nominee_id == voter.id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Votar em si mesmo não vale 😅"
            )
        valid_ids = {u.id for u in individual_nominees(db)}
        if nominee_id not in valid_ids:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Indicado inválido.")
        vote = Vote(voter_id=voter.id, category_id=category_id, nominee_user_id=nominee_id)

    db.add(vote)
    try:
        db.commit()
    except IntegrityError as exc:  # dois cliques simultâneos
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Você já votou nessa categoria.") from exc


def discard_votes_received(db: Session, user: User) -> None:
    db.execute(delete(Vote).where(Vote.nominee_user_id == user.id))
    couple = couple_of(db, user.id)
    if couple:
        db.execute(delete(Vote).where(Vote.nominee_couple_id == couple.id))


def set_partner(db: Session, user: User, partner_id: uuid.UUID | None) -> None:
    if partner_id == user.id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Você não pode ser seu próprio par (por mais que se ame muito).",
        )
    if not has_ticket(db, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Garanta seu ingresso primeiro.")

    partner = None
    if partner_id is not None:
        partner = db.get(User, partner_id)
        if partner is None or not has_ticket(db, partner.id):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Essa pessoa não está entre os confirmados."
            )

    if user.partner_id == partner_id:
        return

    # Trocar ou remover o par desfaz o casal atual (e os votos dele, via ON DELETE CASCADE).
    current = couple_of(db, user.id)
    if current is not None:
        db.delete(current)

    user.partner_id = partner_id
    db.flush()

    if partner is not None and partner.partner_id == user.id:
        a, b = sorted((user.id, partner.id))
        db.add(Couple(user_a_id=a, user_b_id=b))
    db.commit()
