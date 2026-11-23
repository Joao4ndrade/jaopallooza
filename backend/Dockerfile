FROM python:3.13-slim

RUN pip install --no-cache-dir uv==0.11.32

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependências primeiro: aproveita o cache do Docker quando só o código muda.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8000
# Aplica as migrations e sobe a API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
