from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.names import normalize_name

DEFAULT_JWT_SECRET = "dev-secret-troque-em-producao-por-favor-0000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/jaopallooza"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_expires_days: int = 30
    # Nomes (separados por vírgula) que viram admin ao fazer login. Ex.: "João"
    admin_names: str = ""
    # Se preenchido, o cadastro exige esse código (ex.: vai no link do grupo).
    invite_code: str = ""
    # Origens liberadas no CORS, separadas por vírgula.
    cors_origins: str = "http://localhost:5173"

    # Endereço público do site: é para onde o link do e-mail de recuperação aponta.
    frontend_url: str = "http://localhost:5173"
    password_reset_minutes: int = 60

    # SMTP para enviar e-mails. Sem SMTP_HOST, o link de recuperação aparece no log da API.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    # Remetente, ex.: "JAOPALLOOZA <seuemail@gmail.com>". Vazio = usa SMTP_USER.
    smtp_from: str = ""
    # "starttls" (porta 587), "ssl" (porta 465) ou "none"
    smtp_security: str = "starttls"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        # Render, Railway, Heroku etc. entregam "postgres://..."; o SQLAlchemy precisa do driver.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @property
    def admin_name_keys(self) -> set[str]:
        return {normalize_name(n) for n in self.admin_names.split(",") if n.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
