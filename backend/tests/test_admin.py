import pytest

from tests.conftest import category, me


@pytest.fixture
def admin(make_user, settings, monkeypatch):
    monkeypatch.setattr(settings, "admin_names", "Joao, Outra Pessoa")
    return make_user("João")


def test_regular_user_cannot_use_admin(client, make_user):
    ana = make_user("Ana")
    assert client.get("/api/admin/guests", headers=ana).status_code == 403


def test_admin_flag(client, admin):
    assert me(client, admin)["is_admin"] is True


def test_check_in_flow(client, admin, make_user):
    ana = make_user("Ana")
    code = client.get("/api/tickets/me", headers=ana).json()["code"]

    lookup = client.get(f"/api/admin/tickets/{code.lower()}", headers=admin)
    first = client.post(f"/api/admin/tickets/{code}/check-in", headers=admin)
    second = client.post(f"/api/admin/tickets/{code}/check-in", headers=admin)

    assert lookup.json()["holder_name"] == "Ana"
    assert first.status_code == 200
    assert first.json()["checked_in_at"] is not None
    assert second.status_code == 409
    assert client.get("/api/tickets/me", headers=ana).json()["checked_in_at"] is not None
    assert client.get("/api/admin/tickets/JPZ-XXXX-XXXX", headers=admin).status_code == 404


def test_guest_list(client, admin, make_user):
    make_user("Ana")
    make_user("Sem Ingresso", ticket=False)

    names = [g["name"] for g in client.get("/api/admin/guests", headers=admin).json()]
    assert names == ["Ana", "João"]


def test_results(client, admin, make_user):
    ana, beto, carla = make_user("Ana"), make_user("Beto"), make_user("Carla")
    cat = category(client, ana, "mais-atrasado")
    carla_id = me(client, carla)["id"]
    for voter in (ana, beto):
        client.post(f"/api/awards/{cat['id']}/vote", headers=voter, json={"nominee_id": carla_id})
    client.post(
        f"/api/awards/{cat['id']}/vote", headers=carla, json={"nominee_id": me(client, ana)["id"]}
    )

    results = client.get("/api/admin/results", headers=admin).json()
    atrasado = next(r for r in results if r["id"] == cat["id"])
    assert atrasado["total_votes"] == 3
    assert atrasado["ranking"] == [{"name": "Carla", "votes": 2}, {"name": "Ana", "votes": 1}]


def test_update_event_and_add_category(client, admin):
    updated = client.put(
        "/api/admin/event",
        headers=admin,
        json={"venue_name": "Usina Cultural", "starts_at": "2027-03-20T20:00:00-03:00"},
    )
    assert updated.status_code == 200
    event = client.get("/api/event").json()
    assert event["venue_name"] == "Usina Cultural"
    assert event["starts_at"].startswith("2027-03-20T23:00:00")  # salvo em UTC
    assert event["city"] is None

    created = client.post(
        "/api/admin/categories",
        headers=admin,
        json={"slug": "rei-do-karaoke", "title": "Rei/Rainha do karaokê", "emoji": "🎤"},
    )
    assert created.status_code == 201
    assert "rei-do-karaoke" in [
        c["slug"] for c in client.get("/api/awards", headers=admin).json()["categories"]
    ]


def test_reset_password(client, admin, make_user):
    make_user("Ana", password="esqueci1")

    response = client.post(
        "/api/admin/users/reset-password",
        headers=admin,
        json={"name": "ana", "new_password": "nova123"},
    )
    login = client.post("/api/auth/login", json={"login": "Ana", "password": "nova123"})
    assert response.status_code == 200
    assert login.status_code == 200
