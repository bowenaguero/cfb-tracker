from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    # Supabase credentials - required for sync service, optional for worker
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    RECRUITS_TABLE: str = "recruits"
    PORTAL_TABLE: str = "portal"
    # 247Sports config - required for sync service, optional for worker
    TEAM_247_NAME: str | None = None
    TEAM_247_YEAR: int | None = None
    # Redis and team - needed by both sync and worker
    REDIS_URL: str | None = None
    TEAM: str | None = None
    # X (Twitter) API credentials - all optional
    X_API_KEY: str | None = None
    X_API_SECRET: str | None = None
    X_ACCESS_TOKEN: str | None = None
    X_ACCESS_TOKEN_SECRET: str | None = None


config = Config()
