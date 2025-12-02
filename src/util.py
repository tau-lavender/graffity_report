import os
from contextlib import contextmanager
from typing import Optional, Any
import boto3  # type: ignore[import-not-found]
from botocore.client import Config  # type: ignore[import-not-found]
from sqlalchemy import create_engine  # type: ignore[import-not-found]
from sqlalchemy.orm import sessionmaker, Session  # type: ignore[import-not-found]
from src.models import Base, User
from PIL import Image  # type: ignore[import-not-found]
import io


def get_database_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return db_url


def create_db_engine():
    db_url = get_database_url()
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False
    )


def init_db(engine):
    Base.metadata.create_all(engine)


_engine: Any = None
_SessionLocal: Any = None


def setup_database(app):
    global _engine, _SessionLocal

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        app.logger.warning("DATABASE_URL not set, database features disabled")
        return

    try:
        _engine = create_db_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)  # type: ignore[no-redef]
        app.config["DB_ENGINE"] = _engine
        app.logger.info("Database engine initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize database: {e}")
        raise


@contextmanager
def get_db_session():
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call setup_database() first.")

    session = _SessionLocal()  # type: ignore[call-arg]
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_user(db: Session, telegram_user: dict):
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
        db.flush()

    return user


_s3_client = None


def get_s3_client():
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
    s3 = get_s3_client()
    if not s3:
        print("MinIO not configured")
        return

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        existing_buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]

        if bucket not in existing_buckets:
            s3.create_bucket(Bucket=bucket)
            print(f"MinIO bucket '{bucket}' created")
        else:
            print(f"MinIO bucket '{bucket}' exists")
    except Exception as e:
        print(f"MinIO init error: {e}")


def upload_file_to_s3(file_data: bytes, filename: str, content_type: str = 'image/jpeg') -> Optional[str]:
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
        return str(url)
    except Exception as e:
        print(f"Presigned URL error: {e}")
        return None


def get_file_from_s3(s3_key: str) -> Optional[bytes]:
    s3 = get_s3_client()
    if not s3:
        return None

    bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')

    try:
        response = s3.get_object(Bucket=bucket, Key=s3_key)
        body = response['Body'].read()
        return bytes(body) if body else None
    except Exception as e:
        print(f"S3 download error: {e}")
        return None


def delete_file_from_s3(s3_key: str) -> bool:
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


def shakalize(file_data: bytes) -> bytes:
    try:
        Image.MAX_IMAGE_PIXELS = 50_000_000
        with Image.open(io.BytesIO(file_data)) as initial_image:
            fmt = (initial_image.format or '').upper()
            allowed = {"JPEG", "JPG", "PNG", "WEBP"}
            if fmt and fmt not in allowed:
                raise ValueError(f"Неподдерживаемый формат: {fmt}")
            try:
                initial_image.seek(0)
            except Exception:
                pass
            width, height = initial_image.size
            if width <= 0 or height <= 0:
                raise ValueError("Некорректные размеры изображения")
            max_side = 720
            if max(width, height) > max_side:
                if width >= height:
                    new_size = (max_side, int(max_side * height / width))
                else:
                    new_size = (int(max_side * width / height), max_side)
            else:
                new_size = (width, height)
            if initial_image.mode not in ("RGB", "L"):
                working = initial_image.convert("RGB")
            else:
                working = initial_image
            new_image = working.resize(new_size)
            byte_arr = io.BytesIO()
            new_image.save(
                byte_arr,
                format='JPEG',
                quality=80,
                optimize=True,
                progressive=True
            )
            byte_arr.seek(0)
            return byte_arr.getvalue()

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Не удалось обработать изображение: {e}")
