"""
Database utilities and session management.
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker, Session  # type: ignore
from src.models import Base


def get_database_url() -> str:
    """Get DATABASE_URL from environment or raise error."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return db_url


def create_db_engine():
    """Create SQLAlchemy engine with connection pooling."""
    db_url = get_database_url()
    return create_engine(
        db_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
        echo=False  # Set to True for SQL query logging
    )


def init_db(engine):
    """
    Initialize database schema (create all tables).
    Only needed if not using init_db.sql or migrations.
    """
    Base.metadata.create_all(engine)


# Global engine and session factory (initialized in create_app)
_engine = None
_SessionLocal = None


def setup_database(app):
    """
    Setup database engine and session factory for Flask app.
    Call this once during app initialization.
    """
    global _engine, _SessionLocal

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        app.logger.warning("DATABASE_URL not set, database features disabled")
        return

    try:
        _engine = create_db_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        app.config["DB_ENGINE"] = _engine
        app.logger.info("Database engine initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize database: {e}")
        raise


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Usage:
        with get_db_session() as db:
            user = db.query(User).filter_by(user_id=123).first()
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call setup_database() first.")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_user(db: Session, telegram_user: dict):
    """
    Get existing user by telegram user_id or create new one.

    Args:
        db: SQLAlchemy session
        telegram_user: dict with keys: id, username, first_name, last_name

    Returns:
        User object
    """
    from src.models import User

    user_id = telegram_user.get("id")
    if not user_id:
        raise ValueError("telegram_user must have 'id' field")

    user = db.query(User).filter_by(user_id=user_id).first()

    if not user:
        user = User(
            user_id=user_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name")
        )
        db.add(user)
        db.flush()  # Get user_id without committing transaction

    return user
