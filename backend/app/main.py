import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEFAULT_JWT_SECRET, get_settings
from app.routers import admin, auth, awards, event, me, photos, tickets

settings = get_settings()

if settings.jwt_secret == DEFAULT_JWT_SECRET:
    logging.getLogger("uvicorn.error").warning(
        "JWT_SECRET padrão em uso. Ok para desenvolvimento, NUNCA em produção!"
    )

app = FastAPI(
    title="JAOPALLOOZA API",
    version="0.1.0",
    description="Ingressos, votação do Awards e check-in do aniversário mais aguardado do ano.",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok"}


for module in (auth, event, tickets, awards, me, photos, admin):
    api.include_router(module.router)

app.include_router(api)
