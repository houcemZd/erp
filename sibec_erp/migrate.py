import os
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sibec.db")
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def run_migrations() -> None:
    engine = create_engine(DATABASE_URL)
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    with engine.begin() as conn:
        for migration in files:
            sql = migration.read_text(encoding="utf-8")
            conn.execute(text(sql))
            print(f"Applied: {migration.name}")


if __name__ == "__main__":
    run_migrations()
