import io

from PIL import Image

from app.services import photos
from tests.conftest import category, me


def image_bytes(fmt="JPEG", size=(800, 600), color=(200, 30, 20), exif=None) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", size, color)
    kwargs = {"exif": exif} if exif is not None else {}
    image.save(buffer, fmt, **kwargs)
    return buffer.getvalue()


def upload(client, headers, data: bytes, filename="foto.jpg", content_type="image/jpeg"):
    return client.put(
        "/api/me/photo", headers=headers, files={"file": (filename, data, content_type)}
    )


def test_upload_photo_is_square_webp_and_public(client, make_user):
    ana = make_user("Ana")

    response = upload(client, ana, image_bytes(size=(800, 600)))

    assert response.status_code == 200
    photo_url = response.json()["photo_url"]
    assert photo_url.startswith("/photos/")
    served = client.get("/api" + photo_url)  # público: <img> não manda token
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/webp"
    assert "immutable" in served.headers["cache-control"]
    image = Image.open(io.BytesIO(served.content))
    assert image.format == "WEBP"
    assert image.size == (photos.OUTPUT_SIZE, photos.OUTPUT_SIZE)


def test_metadata_like_gps_is_removed(client, make_user):
    ana = make_user("Ana")
    exif = Image.Exif()
    exif[0x010F] = "Apple"  # fabricante
    exif[0x0110] = "iPhone"  # modelo
    exif[0x8825] = {2: (23.0, 32.0, 0.0), 4: (46.0, 38.0, 0.0)}  # GPS
    original = image_bytes(exif=exif.tobytes())
    assert Image.open(io.BytesIO(original)).getexif()  # o original tem EXIF

    photo_url = upload(client, ana, original).json()["photo_url"]
    served = Image.open(io.BytesIO(client.get("/api" + photo_url).content))

    assert not served.getexif()
    assert "exif" not in served.info and "xmp" not in served.info


def test_phone_rotation_is_applied(client, make_user):
    ana = make_user("Ana")
    # Foto "deitada" (largura > altura): metade de cima vermelha, de baixo azul.
    landscape = Image.new("RGB", (600, 400), (255, 0, 0))
    landscape.paste((0, 0, 255), (0, 200, 600, 400))
    exif = Image.Exif()
    exif[0x0112] = 6  # celular: "gire 90° no sentido horário para exibir"
    buffer = io.BytesIO()
    landscape.save(buffer, "JPEG", exif=exif.tobytes())

    photo_url = upload(client, ana, buffer.getvalue()).json()["photo_url"]
    served = Image.open(io.BytesIO(client.get("/api" + photo_url).content)).convert("RGB")

    # Girada, a parte azul fica à esquerda e a vermelha à direita.
    left, right = served.getpixel((20, 192)), served.getpixel((363, 192))
    assert left[2] > 150 and left[0] < 100
    assert right[0] > 150 and right[2] < 100


def test_png_with_transparency_is_accepted(client, make_user):
    ana = make_user("Ana")
    buffer = io.BytesIO()
    Image.new("RGBA", (300, 300), (0, 0, 0, 0)).save(buffer, "PNG")

    response = upload(client, ana, buffer.getvalue(), "foto.png", "image/png")
    assert response.status_code == 200


def test_rejects_files_that_are_not_images(client, make_user):
    ana = make_user("Ana")

    response = upload(client, ana, b"isso nao e uma imagem", "virus.jpg")

    assert response.status_code == 422
    assert me(client, ana)["photo_url"] is None


def test_rejects_huge_files(client, make_user, monkeypatch):
    ana = make_user("Ana")
    monkeypatch.setattr(photos, "MAX_UPLOAD_BYTES", 1000)

    response = upload(client, ana, image_bytes())
    assert response.status_code == 413


def test_replacing_photo_changes_the_address(client, make_user):
    ana = make_user("Ana")
    first = upload(client, ana, image_bytes(color=(255, 0, 0))).json()["photo_url"]
    second = upload(client, ana, image_bytes(color=(0, 255, 0))).json()["photo_url"]

    assert first != second
    assert client.get("/api" + first).status_code == 404
    assert client.get("/api" + second).status_code == 200


def test_remove_photo(client, make_user):
    ana = make_user("Ana")
    photo_url = upload(client, ana, image_bytes()).json()["photo_url"]

    response = client.delete("/api/me/photo", headers=ana)

    assert response.status_code == 200
    assert response.json()["photo_url"] is None
    assert client.get("/api" + photo_url).status_code == 404


def test_photo_requires_login(client):
    response = client.put("/api/me/photo", files={"file": ("f.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 401


def test_deleting_account_removes_photo(client, make_user):
    ana = make_user("Ana")
    photo_url = upload(client, ana, image_bytes()).json()["photo_url"]

    client.delete("/api/me", headers=ana)

    assert client.get("/api" + photo_url).status_code == 404


def test_photo_shows_up_for_nominees_and_partner_options(client, make_user):
    ana, beto = make_user("Ana"), make_user("Beto")
    photo_url = upload(client, ana, image_bytes()).json()["photo_url"]

    nominee = category(client, beto, "mais-atrasado")["nominees"][0]
    options = client.get("/api/me/partner-options", headers=beto).json()

    assert nominee["members"] == [{"name": "Ana", "photo_url": photo_url}]
    assert options == [{"id": me(client, ana)["id"], "name": "Ana", "photo_url": photo_url}]


def test_attendees_list_requires_login_and_shows_ticket_holders(client, make_user):
    ana = make_user("Ana")
    make_user("Beto")
    make_user("Sem Ingresso", ticket=False)
    photo_url = upload(client, ana, image_bytes()).json()["photo_url"]

    assert client.get("/api/event/attendees").status_code == 401
    attendees = client.get("/api/event/attendees", headers=ana).json()

    assert [a["name"] for a in attendees] == ["Ana", "Beto"]
    assert attendees[0]["photo_url"] == photo_url
    assert attendees[1]["photo_url"] is None
