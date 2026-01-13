"""
Production-Ready Database Configuration
Supports both SQLite (dev) and PostgreSQL (production)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool


# Detect environment
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'
DATABASE_URL = os.environ.get('DATABASE_URL')

# PostgreSQL URL fix for Render (uses postgres:// but SQLAlchemy needs postgresql://)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Development: SQLite
if not DATABASE_URL or not IS_PRODUCTION:
    DATABASE_URL = "sqlite:///valuations.sqlite"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool  # SQLite doesn't need connection pooling
    )
    print(f"📊 Using SQLite database: {DATABASE_URL}")

# Production: PostgreSQL
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,  # Number of connections to keep open
        max_overflow=10,  # Max additional connections when pool is full
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False  # Set to True for SQL query logging (debugging only)
    )
    print(f"🐘 Using PostgreSQL database (connection pooling enabled)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_session():
    """Get a new database session"""
    return SessionLocal()


def check_db_health():
    """
    Health check for database connection
    Returns (is_healthy: bool, message: str)
    """
    try:
        session = get_session()
        # Try a simple query
        session.execute("SELECT 1")
        session.close()
        return True, "Database connection healthy"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


# Initialize database on module import
if __name__ != "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database: {e}")
        print("   The application will start but database features may not work.")
