import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")


class Settings(BaseSettings):
    GITHUB_TOKEN: str
    db_user: str = "github_analysis"
    db_password: str = "github_analysis"
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "github_analysis"
    echo_sql: bool = False

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8"
    )

settings = Settings()