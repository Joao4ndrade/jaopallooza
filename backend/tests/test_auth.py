from tests.conftest import me


def register(client, name, email, password="senha123", **extra):
    return client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password, **extra}
    )


def test_register_returns_token_and_me_works(client, make_user):
    headers = make_user("João", ticket=False)

    data = me(client, headers)
    assert data["name"] == "João"
    assert data["email"] == "joao@exemplo.com"
    assert data["has_ticket"] is False
    assert data["is_admin"] is False


def test_email_is_required_and_validated(client, settings):
    no_email = client.post("/api/auth/register", json={"name": "Ana", "password": "senha123"})
    bad_email = register(client, "Ana", "ana-sem-arroba")
    assert no_email.status_code == bad_email.status_code == 422


def test_name_is_unique_ignoring_accents_case_and_spaces(client, make_user):
    make_user("João Pedro", ticket=False)

    response = register(client, "  joao   PEDRO ", "outro@exemplo.com")
    assert response.status_code == 409
    assert "nome" in response.json()["detail"]


def test_email_is_unique_ignoring_case(client, make_user):
    make_user("Ana", ticket=False)

    response = register(client, "Outra Ana", "ANA@Exemplo.com")
    assert response.status_code == 409
    assert "e-mail" in response.json()["detail"]


def test_name_availability_check(client, make_user):
    make_user("João Pedro", ticket=False)

    def check(name):
        return client.get("/api/auth/name-available", params={"name": name}).json()

    assert check("joão pedro")["available"] is False
    assert check("João P.")["available"] is True
    assert check("J")["available"] is False  # curto demais
    assert check("<script>")["available"] is False


def test_login_with_name_or_email(client, make_user):
    make_user("João Pedro", ticket=False, password="festa123")

    by_name = client.post("/api/auth/login", json={"login": "joao pedro", "password": "festa123"})
    by_email = client.post(
        "/api/auth/login", json={"login": " Joao.Pedro@exemplo.com", "password": "festa123"}
    )
    assert by_name.status_code == by_email.status_code == 200
    token = by_email.json()["access_token"]
    assert me(client, {"Authorization": f"Bearer {token}"})["name"] == "João Pedro"


def test_login_with_wrong_password_or_unknown_user(client, make_user):
    make_user("Ana", ticket=False, password="certa123")

    wrong = client.post("/api/auth/login", json={"login": "Ana", "password": "errada123"})
    unknown = client.post("/api/auth/login", json={"login": "Zé", "password": "certa123"})
    unknown_email = client.post(
        "/api/auth/login", json={"login": "ninguem@exemplo.com", "password": "certa123"}
    )
    assert wrong.status_code == unknown.status_code == unknown_email.status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/api/me", headers={"Authorization": "Bearer nada-a-ver"})
    assert response.status_code == 401


def test_name_validation(client, settings):
    for name in ["A", "<script>", "a" * 31]:
        assert register(client, name, "teste@exemplo.com").status_code == 422, name


def test_short_password_is_rejected(client, settings):
    assert register(client, "Ana", "ana@exemplo.com", password="123").status_code == 422


def test_invite_code_when_configured(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "invite_code", "festa2027")

    assert client.get("/api/event").json()["invite_required"] is True
    no_code = register(client, "Penetra", "penetra@exemplo.com")
    wrong = register(client, "Penetra", "penetra@exemplo.com", invite_code="chute")
    ok = register(client, "Convidado", "convidado@exemplo.com", invite_code=" FESTA2027 ")
    assert no_code.status_code == wrong.status_code == 403
    assert ok.status_code == 201
