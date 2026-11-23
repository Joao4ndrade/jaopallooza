from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from sqlalchemy import update

from app.models import PasswordResetToken
from tests.conftest import me


def forgot(client, email):
    return client.post("/api/auth/forgot-password", json={"email": email})


def token_from(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


def test_forgot_password_sends_link_by_email(client, make_user, outbox, settings, monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://jaopallooza.com.br/")
    make_user("Ana", ticket=False)

    response = forgot(client, "ANA@exemplo.com")

    assert response.status_code == 202
    assert len(outbox) == 1
    assert outbox[0]["to"] == "ana@exemplo.com"
    assert outbox[0]["name"] == "Ana"
    assert outbox[0]["link"].startswith("https://jaopallooza.com.br/redefinir-senha?token=")


def test_unknown_email_gets_the_same_answer(client, make_user, outbox):
    make_user("Ana", ticket=False)

    known = forgot(client, "ana@exemplo.com")
    unknown = forgot(client, "ninguem@exemplo.com")

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(outbox) == 1  # só o e-mail que existe recebeu


def test_reset_password_flow(client, make_user, outbox):
    make_user("Ana", ticket=False, password="antiga123")
    forgot(client, "ana@exemplo.com")
    token = token_from(outbox[0]["link"])

    response = client.post("/api/auth/reset-password", json={"token": token, "password": "nova123"})

    assert response.status_code == 200
    new_session = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert me(client, new_session)["name"] == "Ana"
    # senha nova funciona, antiga não
    old_login = client.post("/api/auth/login", json={"login": "Ana", "password": "antiga123"})
    new_login = client.post("/api/auth/login", json={"login": "Ana", "password": "nova123"})
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_reset_logs_out_old_sessions(client, make_user, outbox, db):
    from app.models import User

    ana = make_user("Ana", ticket=False)
    # Simula que o login antigo aconteceu bem antes da troca de senha
    db.execute(update(User).values(password_changed_at=datetime.now(UTC) + timedelta(seconds=5)))
    db.flush()

    assert client.get("/api/me", headers=ana).status_code == 401


def test_reset_link_works_only_once(client, make_user, outbox):
    make_user("Ana", ticket=False)
    forgot(client, "ana@exemplo.com")
    token = token_from(outbox[0]["link"])

    first = client.post("/api/auth/reset-password", json={"token": token, "password": "nova123"})
    second = client.post("/api/auth/reset-password", json={"token": token, "password": "outra123"})

    assert first.status_code == 200
    assert second.status_code == 400


def test_expired_or_fake_link_is_rejected(client, make_user, outbox, db):
    make_user("Ana", ticket=False)
    forgot(client, "ana@exemplo.com")
    token = token_from(outbox[0]["link"])
    db.execute(
        update(PasswordResetToken).values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    db.flush()

    expired = client.post("/api/auth/reset-password", json={"token": token, "password": "nova123"})
    fake = client.post("/api/auth/reset-password", json={"token": "inventado", "password": "x" * 8})

    assert expired.status_code == fake.status_code == 400


def test_new_password_must_be_valid(client, make_user, outbox):
    make_user("Ana", ticket=False)
    forgot(client, "ana@exemplo.com")
    token = token_from(outbox[0]["link"])

    response = client.post("/api/auth/reset-password", json={"token": token, "password": "123"})
    assert response.status_code == 422


def test_resend_has_a_cooldown(client, make_user, outbox):
    make_user("Ana", ticket=False)

    forgot(client, "ana@exemplo.com")
    forgot(client, "ana@exemplo.com")

    assert len(outbox) == 1
