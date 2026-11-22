import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "instance" / "campusride.db"
    secure_cookie: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        local = dotenv_values(ROOT / ".env")
        default_path = "instance/campusride.db"
        path = os.getenv("CAMPUSRIDE_DB_PATH", local.get("CAMPUSRIDE_DB_PATH") or default_path)
        secure = os.getenv(
            "CAMPUSRIDE_SECURE_COOKIE", local.get("CAMPUSRIDE_SECURE_COOKIE") or "false"
        ).lower()
        if secure not in {"true", "false"}:
            raise ValueError("CAMPUSRIDE_SECURE_COOKIE must be true or false.")
        return cls(database_path=(ROOT / path).resolve(), secure_cookie=secure == "true")
