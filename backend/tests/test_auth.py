from tests.conftest import me


def test_register_returns_token_and_me_works(client, make_user):
    headers = make_user("João", ticket=False)

    data = me(client, headers)
    assert data["name"] == "João"
    assert data["has_ticket"] is False
    assert data["is_admin"] is False


def test_name_is_unique_ignoring_accents_case_and_spaces(client, make_user):
    make_user("João Pedro", ticket=False)

    response = client.post(
        "/api/auth/register", json={"name": "  joao   PEDRO ", "password": "outrasenha"}
    )
    assert response.status_code == 409


def test_login_accepts_any_casing_and_accents(client, make_user):
    make_user("João Pedro", ticket=False, password="festa123")

    response = client.post("/api/auth/login", json={"name": "joao pedro", "password": "festa123"})
    assert response.status_code == 200
    assert (
        me(client, {"Authorization": f"Bearer {response.json()['access_token']}"})["name"]
        == "João Pedro"
    )


def test_login_with_wrong_password_or_unknown_name(client, make_user):
    make_user("Ana", ticket=False, password="certa123")

    wrong = client.post("/api/auth/login", json={"name": "Ana", "password": "errada123"})
    unknown = client.post("/api/auth/login", json={"name": "Zé", "password": "certa123"})
    assert wrong.status_code == unknown.status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/api/me", headers={"Authorization": "Bearer nada-a-ver"})
    assert response.status_code == 401


def test_name_validation(client, settings):
    for name in ["A", "<script>", "a" * 31]:
        response = client.post("/api/auth/register", json={"name": name, "password": "senha123"})
        assert response.status_code == 422, name


def test_short_password_is_rejected(client, settings):
    response = client.post("/api/auth/register", json={"name": "Ana", "password": "123"})
    assert response.status_code == 422


def test_invite_code_when_configured(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "invite_code", "festa2027")

    assert client.get("/api/event").json()["invite_required"] is True
    no_code = client.post("/api/auth/register", json={"name": "Penetra", "password": "senha123"})
    wrong = client.post(
        "/api/auth/register",
        json={"name": "Penetra", "password": "senha123", "invite_code": "chute"},
    )
    ok = client.post(
        "/api/auth/register",
        json={"name": "Convidado", "password": "senha123", "invite_code": " FESTA2027 "},
    )
    assert no_code.status_code == wrong.status_code == 403
    assert ok.status_code == 201
