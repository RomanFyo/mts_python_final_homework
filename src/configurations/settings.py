from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # for PostgreSQL
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str
    jwt_secret_key: str
    access_token_expire_minutes: int
    db_test_name: str = "fastapi_project_test_db"
    max_connection_count: int = 10

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_test_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_test_name}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")


settings = Settings()
