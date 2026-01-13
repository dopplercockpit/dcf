import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool


IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL or not IS_PRODUCTION:
    DATABASE_URL = "sqlite:///valuations.sqlite"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    print(f"Using SQLite database: {DATABASE_URL}")
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    print("Using PostgreSQL database (connection pooling enabled)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a new database session."""
    return SessionLocal()


def check_db_health():
    """Return (is_healthy, message) for database connectivity."""
    session = get_session()
    try:
        session.execute(text("SELECT 1"))
        return True, "Database connection healthy"
    except Exception as exc:
        return False, f"Database connection failed: {exc}"
    finally:
        session.close()
