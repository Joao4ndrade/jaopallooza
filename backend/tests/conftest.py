import os
from collections.abc import Callable
from pathlib import Path

# Precisa vir antes de importar o app: o engine é criado com essa URL.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/jaopallooza_test"
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]

Headers = dict[str, str]


@pytest.fixture(scope="session")
def engine():
    url = get_settings().database_url
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    # Roda as migrations de verdade: testa o schema que vai para produção.
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """Cada teste roda numa transação que é desfeita no final (banco sempre limpo)."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def _override():
        try:
            yield db
        finally:
            db.expire_all()  # simula uma sessão nova a cada request

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def settings(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "admin_names", "")
    monkeypatch.setattr(s, "invite_code", "")
    return s


@pytest.fixture
def make_user(client, settings) -> Callable[..., Headers]:
    def _make(name: str, *, ticket: bool = True, password: str = "senha123") -> Headers:
        response = client.post("/api/auth/register", json={"name": name, "password": password})
        assert response.status_code == 201, response.text
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        if ticket:
            assert client.post("/api/tickets", headers=headers).status_code == 201
        return headers

    return _make


def category(client: TestClient, headers: Headers, slug: str) -> dict:
    data = client.get("/api/awards", headers=headers).json()
    return next(c for c in data["categories"] if c["slug"] == slug)


def me(client: TestClient, headers: Headers) -> dict:
    return client.get("/api/me", headers=headers).json()
