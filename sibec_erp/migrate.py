import os
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sibec.db")
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def run_migrations() -> None:
    engine = create_engine(DATABASE_URL)
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        applied = {
            row[0]
            for row in conn.execute(text("SELECT filename FROM schema_migrations")).fetchall()
        }

        for migration in files:
            if migration.name in applied:
                print(f"Skipped (already applied): {migration.name}")
                continue
            sql = migration.read_text(encoding="utf-8")
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations(filename) VALUES (:filename)"),
                {"filename": migration.name},
            )
            print(f"Applied: {migration.name}")


if __name__ == "__main__":
    run_migrations()
