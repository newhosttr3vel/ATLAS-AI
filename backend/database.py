"""Database configuration and request-scoped SQLAlchemy sessions."""

import os
from pathlib import Path
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/atlas_ai.db")

if DATABASE_URL.startswith("sqlite:///") and ":memory:" not in DATABASE_URL:
    sqlite_path = DATABASE_URL.removeprefix("sqlite:///").split("?", maxsplit=1)[0]
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per API request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
