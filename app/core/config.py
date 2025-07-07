from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key"
    REFRESH_SECRET_KEY: str = "dev-refresh-secret"
    DATABASE_URL: str = "sqlite:///./test.db"
    # Add other settings as needed

    model_config = SettingsConfigDict(env_file=".env")

    def validate(self):
        missing = []
        for field in ["SECRET_KEY", "REFRESH_SECRET_KEY", "DATABASE_URL"]:
            if not getattr(self, field, None):
                missing.append(field)
        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.critical(msg)
            raise RuntimeError(msg)

settings = Settings()
settings.validate()