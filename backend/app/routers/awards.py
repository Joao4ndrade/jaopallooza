from fastapi import APIRouter, status

from app.deps import DB, CurrentUser
from app.schemas import AwardsOut, CategoryOut, VoteIn
from app.services import awards

router = APIRouter(prefix="/awards", tags=["awards"])


@router.get("")
def list_categories(user: CurrentUser, db: DB) -> AwardsOut:
    return AwardsOut(
        can_vote=awards.has_ticket(db, user.id),
        categories=awards.build_categories(db, user),
    )


@router.post("/{category_id}/vote", status_code=status.HTTP_201_CREATED)
def vote(category_id: int, data: VoteIn, user: CurrentUser, db: DB) -> CategoryOut:
    awards.cast_vote(db, user, category_id, data.nominee_id)
    return next(c for c in awards.build_categories(db, user) if c.id == category_id)
