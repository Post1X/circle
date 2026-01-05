from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Literal


class Setings(BaseSettings):
    db_name: str
    db_pass: str
    db_host: str
    db_port: int
    db_user: str
    mode: Literal["test", "prod"] = "prod"

    ALGORITHM: str
    SECRET_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int

    mnemonic: str
    tron_api_key: str
    ENCRYPTION_KEY: str

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


config = Setings()
