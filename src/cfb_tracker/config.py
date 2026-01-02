from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    RECRUITS_TABLE: str = "recruits"
    PORTAL_TABLE: str = "portal"
    TEAM_247_NAME: str
    TEAM_247_YEAR: int
    REDIS_URL: str | None = None
    TEAM: str


config = Config()
