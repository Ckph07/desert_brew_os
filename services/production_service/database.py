"""
Database configuration for Production Service.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Normalized DB settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "desertbrew")
DB_PASSWORD = os.getenv("DB_PASSWORD", "desertbrew123")
DB_NAME = os.getenv("DB_NAME", "production_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_upgrades() -> None:
    """
    Apply lightweight schema upgrades for deployments without Alembic.

    This keeps existing local/dev databases compatible when new columns are
    introduced in models.
    """
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "production_batches" not in table_names:
        return

    columns = {col["name"] for col in inspector.get_columns("production_batches")}
    if "recipe_snapshot" in columns:
        return

    dialect = engine.dialect.name
    column_type = "JSON" if dialect == "postgresql" else "TEXT"
    with engine.begin() as conn:
        conn.execute(
            text(
                f"ALTER TABLE production_batches "
                f"ADD COLUMN recipe_snapshot {column_type}"
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
