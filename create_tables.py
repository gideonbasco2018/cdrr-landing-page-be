"""Dev-only: create all tables directly from the SQLAlchemy models,
bypassing Alembic. Useful for quick local iteration.

Usage:
    python create_tables.py
"""

from app.db.database import Base, engine
from app.models import user  # noqa: F401  (ensures model is registered on Base)


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    main()
