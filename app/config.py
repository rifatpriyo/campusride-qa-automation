import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "instance" / "campusride.db"
    secure_cookie: bool = False
    demo_bug_mode: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        local = dotenv_values(ROOT / ".env")
        default_path = "instance/campusride.db"
        path = os.getenv("CAMPUSRIDE_DB_PATH", local.get("CAMPUSRIDE_DB_PATH") or default_path)

        def flag(name: str) -> bool:
            value = os.getenv(name, local.get(name) or "false").lower()
            if value not in {"true", "false"}:
                raise ValueError(f"{name} must be true or false.")
            return value == "true"

        return cls(
            database_path=(ROOT / path).resolve(),
            secure_cookie=flag("CAMPUSRIDE_SECURE_COOKIE"),
            demo_bug_mode=flag("DEMO_BUG_MODE"),
        )
