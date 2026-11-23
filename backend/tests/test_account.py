from tests.conftest import category, me


def test_partner_rules(client, make_user):
    ana = make_user("Ana")
    sem_ingresso = make_user("Sem Ingresso", ticket=False)
    ana_id = me(client, ana)["id"]

    myself = client.put("/api/me/partner", headers=ana, json={"partner_id": ana_id})
    not_confirmed = client.put(
        "/api/me/partner", headers=ana, json={"partner_id": me(client, sem_ingresso)["id"]}
    )
    no_ticket = client.put("/api/me/partner", headers=sem_ingresso, json={"partner_id": ana_id})

    assert myself.status_code == 422
    assert not_confirmed.status_code == 404
    assert no_ticket.status_code == 403


def test_partner_options_lists_other_ticket_holders(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")
    make_user("Sem Ingresso", ticket=False)

    options = client.get("/api/me/partner-options", headers=ana).json()
    assert [o["name"] for o in options] == ["Beto"]


def test_delete_account_cleans_everything(client, make_user):
    ana, beto, carla = make_user("Ana"), make_user("Beto"), make_user("Carla")
    ana_id = me(client, ana)["id"]
    client.put("/api/me/partner", headers=ana, json={"partner_id": me(client, beto)["id"]})
    client.put("/api/me/partner", headers=beto, json={"partner_id": ana_id})
    cat = category(client, carla, "mais-engracado")
    client.post(f"/api/awards/{cat['id']}/vote", headers=carla, json={"nominee_id": ana_id})

    response = client.delete("/api/me", headers=ana)

    assert response.status_code == 204
    assert client.get("/api/me", headers=ana).status_code == 401
    assert me(client, beto)["partner_status"] == "none"
    assert category(client, carla, "mais-engracado")["my_vote"] is None
    assert category(client, carla, "melhor-casal")["nominees"] == []
    assert client.get("/api/event").json()["tickets_count"] == 2
    # O nome fica livre de novo
    again = client.post(
        "/api/auth/register",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha123"},
    )
    assert again.status_code == 201


def test_change_email(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")

    taken = client.put("/api/me/email", headers=ana, json={"email": "BETO@exemplo.com"})
    invalid = client.put("/api/me/email", headers=ana, json={"email": "nao-e-email"})
    ok = client.put("/api/me/email", headers=ana, json={"email": " Ana.Nova@Exemplo.com "})

    assert taken.status_code == 409
    assert invalid.status_code == 422
    assert ok.status_code == 200
    assert ok.json()["email"] == "ana.nova@exemplo.com"
