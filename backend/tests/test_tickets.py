import re


def test_event_starts_with_everything_em_breve(client):
    event = client.get("/api/event").json()

    assert event["name"] == "JAOPALLOOZA 2027"
    assert event["starts_at"] is None
    assert event["venue_name"] is None
    assert event["tickets_count"] == 0


def test_claim_ticket_is_idempotent(client, make_user):
    headers = make_user("Ana", ticket=False)

    first = client.post("/api/tickets", headers=headers)
    second = client.post("/api/tickets", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["code"] == second.json()["code"]
    assert re.fullmatch(r"JPZ-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}", first.json()["code"])
    assert first.json()["holder_name"] == "Ana"
    assert client.get("/api/event").json()["tickets_count"] == 1


def test_my_ticket(client, make_user):
    headers = make_user("Ana", ticket=False)
    assert client.get("/api/tickets/me", headers=headers).status_code == 404

    code = client.post("/api/tickets", headers=headers).json()["code"]
    response = client.get("/api/tickets/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == code
    assert response.json()["checked_in_at"] is None


def test_ticket_requires_login(client):
    assert client.post("/api/tickets").status_code == 401
