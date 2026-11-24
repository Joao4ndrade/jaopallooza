"""Tratamento das fotos de perfil.

Toda foto é regravada do zero: sai quadrada, 384x384, em WebP e SEM metadados.
Isso importa porque foto de celular costuma carregar a localização GPS de onde foi
tirada, e as fotos aqui ficam visíveis para a galera toda.
"""

import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
OUTPUT_SIZE = 384
CONTENT_TYPE = "image/webp"
# MPO é o "JPEG" de algumas câmeras/celulares.
_ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP", "GIF"}
# Acima disso o Pillow recusa (proteção contra "bomba de descompressão").
Image.MAX_IMAGE_PIXELS = 50_000_000


class InvalidImage(ValueError):
    pass


def process_photo(raw: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in _ALLOWED_FORMATS:
                raise InvalidImage("Formato não suportado. Use uma foto JPG, PNG ou WebP.")
            source.load()
            # Celular salva a foto "deitada" + uma etiqueta de rotação: aplica a rotação.
            image = ImageOps.exif_transpose(source)
    except InvalidImage:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise InvalidImage("Não consegui ler essa imagem. Tenta outra foto?") from exc

    image = _to_rgb(image)

    # Recorte quadrado. Em foto "em pé", puxa o recorte para cima, onde costuma estar o rosto.
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = int((height - side) * 0.3) if height > width else 0
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

    # Imagem nova "em branco" + pixels: garante que nenhum metadado (EXIF, GPS, XMP) sobrevive.
    clean = Image.new("RGB", image.size)
    clean.paste(image)
    output = io.BytesIO()
    clean.save(output, "WEBP", quality=82, method=6)
    return output.getvalue()


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA", "P", "PA"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")
