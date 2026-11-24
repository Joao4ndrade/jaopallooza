from tests.conftest import category, me


def nominee_names(cat: dict) -> list[str]:
    return [n["name"] for n in cat["nominees"]]


def test_without_ticket_cannot_vote(client, make_user):
    make_user("Ana")
    visitor = make_user("Visitante", ticket=False)
    cat = category(client, visitor, "mais-atrasado")

    assert client.get("/api/awards", headers=visitor).json()["can_vote"] is False
    response = client.post(
        f"/api/awards/{cat['id']}/vote",
        headers=visitor,
        json={"nominee_id": cat["nominees"][0]["id"]},
    )
    assert response.status_code == 403


def test_nominees_are_ticket_holders_except_me(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")
    make_user("Sem Ingresso", ticket=False)

    cat = category(client, ana, "mais-atrasado")
    assert nominee_names(cat) == ["Beto"]
    assert cat["i_am_nominee"] is True


def test_vote_only_once_per_category(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")
    make_user("Carla")
    cat = category(client, ana, "mais-atrasado")
    beto, carla = cat["nominees"]

    first = client.post(
        f"/api/awards/{cat['id']}/vote", headers=ana, json={"nominee_id": beto["id"]}
    )
    again = client.post(
        f"/api/awards/{cat['id']}/vote", headers=ana, json={"nominee_id": carla["id"]}
    )

    assert first.status_code == 201
    assert first.json()["my_vote"]["nominee"]["name"] == "Beto"
    assert again.status_code == 409
    # Votar em uma categoria não interfere nas outras
    other = category(client, ana, "mais-engracado")
    assert other["my_vote"] is None


def test_cannot_vote_for_yourself(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")
    cat = category(client, ana, "mais-engracado")

    response = client.post(
        f"/api/awards/{cat['id']}/vote", headers=ana, json={"nominee_id": me(client, ana)["id"]}
    )
    assert response.status_code == 422


def test_couple_needs_mutual_confirmation(client, make_user):
    ana, beto, carla = make_user("Ana"), make_user("Beto"), make_user("Carla")
    ana_id, beto_id = me(client, ana)["id"], me(client, beto)["id"]

    after_ana = client.put("/api/me/partner", headers=ana, json={"partner_id": beto_id}).json()
    assert after_ana["partner_status"] == "pending"
    assert [p["name"] for p in me(client, beto)["partner_requests"]] == ["Ana"]
    assert category(client, carla, "melhor-casal")["nominees"] == []

    after_beto = client.put("/api/me/partner", headers=beto, json={"partner_id": ana_id}).json()
    assert after_beto["partner_status"] == "confirmed"
    assert after_beto["partner_requests"] == []
    assert "Melhor casal" in [c["title"] for c in after_beto["competing_in"]]

    couple_cat = category(client, carla, "melhor-casal")
    assert nominee_names(couple_cat) == ["Ana & Beto"]
    assert [m["name"] for m in couple_cat["nominees"][0]["members"]] == ["Ana", "Beto"]
    # O próprio casal não aparece como opção para quem está nele
    assert category(client, ana, "melhor-casal")["nominees"] == []
    assert category(client, ana, "melhor-casal")["i_am_nominee"] is True


def test_cannot_vote_for_own_couple(client, make_user):
    ana, beto, carla = make_user("Ana"), make_user("Beto"), make_user("Carla")
    client.put("/api/me/partner", headers=ana, json={"partner_id": me(client, beto)["id"]})
    client.put("/api/me/partner", headers=beto, json={"partner_id": me(client, ana)["id"]})
    couple = category(client, carla, "melhor-casal")["nominees"][0]

    response = client.post(
        f"/api/awards/{category(client, ana, 'melhor-casal')['id']}/vote",
        headers=ana,
        json={"nominee_id": couple["id"]},
    )
    assert response.status_code == 422


def test_breaking_up_discards_votes_and_gives_vote_back(client, make_user):
    ana, beto, carla = make_user("Ana"), make_user("Beto"), make_user("Carla")
    client.put("/api/me/partner", headers=ana, json={"partner_id": me(client, beto)["id"]})
    client.put("/api/me/partner", headers=beto, json={"partner_id": me(client, ana)["id"]})
    cat = category(client, carla, "melhor-casal")
    client.post(
        f"/api/awards/{cat['id']}/vote",
        headers=carla,
        json={"nominee_id": cat["nominees"][0]["id"]},
    )
    assert category(client, carla, "melhor-casal")["my_vote"] is not None

    after = client.put("/api/me/partner", headers=ana, json={"partner_id": None}).json()

    assert after["partner_status"] == "none"
    # Beto continua apontando para Ana, então vira um "pedido" pendente para ela
    assert [p["name"] for p in after["partner_requests"]] == ["Beto"]
    cat = category(client, carla, "melhor-casal")
    assert cat["nominees"] == []
    assert cat["my_vote"] is None


def test_leaving_the_awards(client, make_user):
    ana, beto = make_user("Ana"), make_user("Beto")
    cat = category(client, beto, "mais-atrasado")
    client.post(
        f"/api/awards/{cat['id']}/vote", headers=beto, json={"nominee_id": me(client, ana)["id"]}
    )

    after = client.put("/api/me/awards", headers=ana, json={"opt_in": False}).json()

    assert after["awards_opt_in"] is False
    assert after["competing_in"] == []
    cat = category(client, beto, "mais-atrasado")
    assert cat["nominees"] == []  # Ana sumiu da lista
    assert cat["my_vote"] is None  # e o voto do Beto voltou pra ele
    # Quem sai continua podendo votar
    ana_cat = category(client, ana, "mais-atrasado")
    assert ana_cat["i_am_nominee"] is False
    response = client.post(
        f"/api/awards/{ana_cat['id']}/vote",
        headers=ana,
        json={"nominee_id": me(client, beto)["id"]},
    )
    assert response.status_code == 201

    back = client.put("/api/me/awards", headers=ana, json={"opt_in": True}).json()
    assert len(back["competing_in"]) == 2  # as duas individuais (sem casal)


def test_inactive_category_is_hidden(client, make_user, db):
    from app.models import AwardCategory

    ana = make_user("Ana")
    db.query(AwardCategory).filter_by(slug="mais-engracado").update({"is_active": False})
    db.flush()

    slugs = [c["slug"] for c in client.get("/api/awards", headers=ana).json()["categories"]]
    assert slugs == ["mais-atrasado", "melhor-casal"]
