"""Regras de nome de usuário.

O login é feito só com nome + senha, então o nome precisa ser único. Para evitar
"João" e "joao" virarem duas contas diferentes, comparamos sempre a versão
normalizada (sem acentos, sem diferença de maiúsculas e com espaços colapsados).
"""

import re
import unicodedata

NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 .'\-]+$")


def clean_name(raw: str) -> str:
    """Remove espaços nas pontas e colapsa espaços repetidos."""
    return " ".join(raw.split())


def normalize_name(raw: str) -> str:
    """Chave usada para unicidade e login: 'João  Pedro' -> 'joao pedro'."""
    decomposed = unicodedata.normalize("NFKD", clean_name(raw))
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.casefold()
