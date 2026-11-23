"""dados iniciais: evento (tudo "em breve") e categorias do Awards

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-22 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DESCRIPTION = (
    "Prepara o look, chama a galera e aquece a voz: o aniversário do João virou festival! 🎪\n\n"
    "Data, local e line-up ainda estão sendo fechados. Assim que tiver novidade, ela aparece "
    "aqui. Enquanto isso, garanta seu ingresso para confirmar presença e já vai votando no "
    "JAOPALLOOZA Awards."
)

CATEGORIES = [
    {
        "slug": "mais-atrasado",
        "title": "Mais atrasado(a)",
        "description": "Aquela pessoa que manda “tô chegando” ainda no banho.",
        "emoji": "⏰",
        "kind": "individual",
        "position": 10,
    },
    {
        "slug": "mais-engracado",
        "title": "Mais engraçado(a)",
        "description": "Transforma qualquer rolê em stand-up.",
        "emoji": "😂",
        "kind": "individual",
        "position": 20,
    },
    {
        "slug": "melhor-casal",
        "title": "Melhor casal",
        "description": "O casal mais casal do rolê. Só concorre quem se confirmou como par na aba Conta.",
        "emoji": "💘",
        "kind": "couple",
        "position": 30,
    },
]


def upgrade() -> None:
    event_info = sa.table(
        "event_info",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("tagline", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        event_info,
        [
            {
                "id": 1,
                "name": "JAOPALLOOZA 2027",
                "tagline": "O aniversário do João com cara de festival",
                "description": DESCRIPTION,
            }
        ],
    )

    categories = sa.table(
        "award_categories",
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.String),
        sa.column("emoji", sa.String),
        sa.column("kind", sa.String),
        sa.column("position", sa.Integer),
    )
    op.bulk_insert(categories, CATEGORIES)


def downgrade() -> None:
    slugs = ", ".join(f"'{c['slug']}'" for c in CATEGORIES)
    op.execute(f"DELETE FROM award_categories WHERE slug IN ({slugs})")
    op.execute("DELETE FROM event_info WHERE id = 1")
