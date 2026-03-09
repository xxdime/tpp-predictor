import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


def get_db_path() -> Path:
    app_data = Path(os.environ.get("APPDATA") or Path.home() / ".local" / "share")
    db_dir = app_data / "tpp-predictor"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "tpp_predictor.db"


def create_db_engine():
    db_path = get_db_path()
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    return SessionLocal()


def init_db():
    from app.models import template, part, measurement, forecast_settings  # noqa
    Base.metadata.create_all(bind=engine)
