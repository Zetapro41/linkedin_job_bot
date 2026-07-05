import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    database_path: Path
    check_interval_hours: int
    limit_results: int
    venice_api_key: str
    venice_model: str
    xai_api_key: str
    xai_model: str

def _default_database_path() -> Path:
    if os.getenv("DATABASE_PATH"):
        return Path(os.getenv("DATABASE_PATH", "linkedin_bot.db"))
    return Path("linkedin_bot.db")

def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        database_path=_default_database_path(),
        check_interval_hours=int(os.getenv("CHECK_INTERVAL_HOURS", "12")),
        limit_results=int(os.getenv("LIMIT_RESULTS", "25")),
        venice_api_key=os.getenv("VENICE_API_KEY", ""),
        venice_model=os.getenv("VENICE_MODEL", "llama-3.3-70b"),
        xai_api_key=os.getenv("XAI_API_KEY", ""),
        xai_model=os.getenv("XAI_MODEL", "grok-3-mini"),
    )