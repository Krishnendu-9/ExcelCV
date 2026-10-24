"""Database layer — SQLAlchemy models shared by Streamlit app and FastAPI backend."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Engine,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(_DB_DIR, exist_ok=True)

DB_PATH = os.path.join(_DB_DIR, "excelcv.db")

# How long a connection waits for a competing writer before raising "database is
# locked". Python's sqlite3 driver already defaults to 5 s; setting it explicitly keeps
# it independent of driver defaults, and 15 s lets a write queued behind a slow
# comparison save wait instead of failing.
SQLITE_BUSY_TIMEOUT_MS = 15000


def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    """Configure every new SQLite connection.

    - foreign_keys: enforce FK constraints.
    - busy_timeout: wait for locks instead of failing at once. Set before journal_mode,
      which itself needs a brief lock.
    - journal_mode=WAL: readers no longer block the writer (or the reverse), which
      matters because Streamlit sessions share this engine across threads. WAL is a
      persistent property of the database file and adds -wal / -shm files beside it.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_sqlite_engine(path: str) -> Engine:
    """Create a thread-shared SQLite engine with the connection pragmas above."""
    new_engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    event.listen(new_engine, "connect", _set_sqlite_pragma)
    return new_engine


engine = create_sqlite_engine(DB_PATH)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, default="GOOGLE_OAUTH"
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="My Resume")
    template: Mapped[str] = mapped_column(String(50), nullable=False, default="classic")
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cv_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Comparison(Base):
    """A persisted multi-resume comparison run.

    ``rows`` stores the full ranked-row list (including each row's stashed
    ``_analysis`` dict) so the report page can be fully reconstructed from
    just this record — no re-running the model, no losing drill-down detail.
    ``errors`` / ``warnings`` are also persisted so partial-failure context
    is preserved when the user revisits a saved comparison.
    """

    __tablename__ = "comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    rows: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    resume_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    top_resume_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def _migrate() -> None:
    """Apply additive SQLite migrations that create_all cannot handle."""
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
        if "google_id" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
            conn.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate()


def get_db() -> Session:
    return SessionLocal()
