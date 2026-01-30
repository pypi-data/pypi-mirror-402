from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class MTXSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MTX_")

    base_url: str | None = None
    client_id: str | None = None
    jwt_secret: str | None = None
