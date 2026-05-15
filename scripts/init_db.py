import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.backend.app.core.database import SessionLocal, init_db
from src.backend.app.services.seed import seed_database


def main() -> None:
    init_db()
    with SessionLocal() as db:
        seed_database(db)
    print("Database initialized and seeded.")


if __name__ == "__main__":
    main()
