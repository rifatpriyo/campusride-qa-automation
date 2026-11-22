from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event


def open_database(path: Path) -> Engine:
    engine = create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"timeout": 10, "check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
