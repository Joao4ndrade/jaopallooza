from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status
from sqlalchemy import select

from app.deps import DB
from app.models import User, UserPhoto

router = APIRouter(prefix="/photos", tags=["fotos"])


@router.get("/{key}", summary="Foto de perfil (endereço muda a cada troca de foto)")
def get_photo(key: Annotated[str, Path(max_length=64)], db: DB) -> Response:
    row = db.execute(
        select(UserPhoto.data, UserPhoto.content_type)
        .join(User, User.id == UserPhoto.user_id)
        .where(User.photo_key == key)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto não encontrada.")
    return Response(
        content=row.data,
        media_type=row.content_type,
        # A chave muda quando a foto muda, então dá para guardar em cache "para sempre".
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
