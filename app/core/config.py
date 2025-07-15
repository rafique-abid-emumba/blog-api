from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
from typing import ClassVar, List

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key"
    REFRESH_SECRET_KEY: str = "dev-refresh-secret"
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    GROQ_API_KEY: str = "dev-groq-api-key"
    LLM_MODEL: str = "deepseek-r1-distill-llama-70b"

    REQUIRED_ENV_VARS: ClassVar[List[str]] = [
        "SECRET_KEY", "REFRESH_SECRET_KEY", "DATABASE_URL", "REDIS_URL", "GROQ_API_KEY", "LLM_MODEL"
    ]

    model_config = SettingsConfigDict(env_file=".env")

    def validate(self):
        missing = []
        for field in self.REQUIRED_ENV_VARS:
            if not getattr(self, field, None):
                missing.append(field)
        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.critical(msg)
            raise RuntimeError(msg)

settings = Settings()
settings.validate()
