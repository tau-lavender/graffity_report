"""
Database utilities and session management.
"""
import os
from contextlib import contextmanager
from typing import Optional
import boto3  # type: ignore
from botocore.client import Config  # type: ignore
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


# ============================================================
# MinIO / S3 Storage utilities
# ============================================================

_s3_client = None


def get_s3_client():
    """Get MinIO/S3 client (singleton)."""
    global _s3_client

    if _s3_client is not None:
        return _s3_client

    endpoint = os.environ.get('MINIO_ENDPOINT')
    access_key = os.environ.get('MINIO_ACCESS_KEY')
    secret_key = os.environ.get('MINIO_SECRET_KEY')

    if not all([endpoint, access_key, secret_key]):
        return None

    _s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

    return _s3_client


def init_minio():
    """Initialize MinIO bucket if not exists."""
    s3 = get_s3_client()
    if not s3:
        print("⚠️  MinIO not configured (MINIO_ENDPOINT not set)")
        return

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        # Проверяем существование bucket
        existing_buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]

        if bucket not in existing_buckets:
            s3.create_bucket(Bucket=bucket)
            print(f"✅ MinIO bucket '{bucket}' created")
        else:
            print(f"✅ MinIO bucket '{bucket}' exists")
    except Exception as e:
        print(f"⚠️  MinIO init error: {e}")


def upload_file_to_s3(file_data: bytes, filename: str, content_type: str = 'image/jpeg') -> Optional[str]:
    """
    Upload file to MinIO/S3.

    Args:
        file_data: File bytes
        filename: Target filename (key) in bucket
        content_type: MIME type

    Returns:
        S3 key (filename) on success, None on failure
    """
    s3 = get_s3_client()
    if not s3:
        return None

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        s3.put_object(
            Bucket=bucket,
            Key=filename,
            Body=file_data,
            ContentType=content_type
        )
        return filename
    except Exception as e:
        print(f"S3 upload error: {e}")
        return None


def get_file_url(s3_key: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generate presigned URL for file download.

    Args:
        s3_key: S3 object key (filename)
        expires_in: URL expiration time in seconds (default 1 hour)

    Returns:
        Presigned URL or None
    """
    s3 = get_s3_client()
    if not s3:
        return None

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f"Presigned URL error: {e}")
        return None


def get_file_from_s3(s3_key: str) -> Optional[bytes]:
    """
    Download file from MinIO/S3.

    Args:
        s3_key: S3 object key (filename)

    Returns:
        File bytes or None
    """
    s3 = get_s3_client()
    if not s3:
        return None

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        response = s3.get_object(Bucket=bucket, Key=s3_key)
        return response['Body'].read()
    except Exception as e:
        print(f"S3 download error: {e}")
        return None


def delete_file_from_s3(s3_key: str) -> bool:
    """Delete file from MinIO/S3."""
    s3 = get_s3_client()
    if not s3:
        return False

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        s3.delete_object(Bucket=bucket, Key=s3_key)
        return True
    except Exception as e:
        print(f"S3 delete error: {e}")
        return False
