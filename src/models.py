from datetime import datetime
from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
    Index,
    text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Таблица пользователей Telegram"""

    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)  # Уникальный ID из Telegram API
    username = Column(String(255), nullable=True)  # Имя пользователя (@username)
    first_name = Column(String(255), nullable=True)  # Имя из профиля Telegram
    last_name = Column(String(255), nullable=True)  # Фамилия из профиля Telegram
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)  # Время регистрации
    is_deleted = Column(Boolean, default=False, nullable=False)  # Мягкое удаление

    reports = relationship("GraffitiReport", back_populates="user")

    def __repr__(self):
        return f"<User({self.user_id})>"


class GraffitiReport(Base):
    """Таблица жалоб на незаконное граффити"""

    __tablename__ = "graffiti_reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)  # Автоинкрементный ID заявки
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)  # Ссылка на пользователя
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)  # Координаты (долгота, широта) в WGS84
    fias_id = Column(UUID(as_uuid=True), nullable=True)  # Уникальный ID адреса из ФИАС (DaData)
    normalized_address = Column(Text, nullable=True)  # Адрес после нормализации через DaData
    status = Column(String(20), default="pending", nullable=False)  # Статус: 'pending', 'approved', 'declined'
    description = Column(Text, nullable=True)  # Комментарий пользователя
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)  # Время создания заявки
    is_deleted = Column(Boolean, default=False, nullable=False)  # Мягкое удаление

    user = relationship("User", back_populates="reports")
    photos = relationship("ReportPhoto", back_populates="report")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'declined')", name="check_status_values"),
        Index('idx_graffiti_reports_location', 'location', postgresql_using='gist'),
        Index('idx_reports_active', 'is_deleted'),  # Ускоряет фильтрацию активных записей (не удаленных)
    )

    def __repr__(self):
        return f"<GraffitiReport({self.report_id})>"


class ReportPhoto(Base):
    """Таблица фотографий, приложенных к заявкам"""

    __tablename__ = "report_photos"

    photo_id = Column(Integer, primary_key=True, autoincrement=True)  # ID фото
    report_id = Column(Integer, ForeignKey("graffiti_reports.report_id"), nullable=False)  # Ссылка на заявку
    s3_key = Column(String(255), nullable=False)  # Ключ объекта в MinIO (путь к файлу)
    uploaded_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)  # Время загрузки
    is_deleted = Column(Boolean, default=False, nullable=False)  # Мягкое удаление

    report = relationship("GraffitiReport", back_populates="photos")

    def __repr__(self):
        return f"<ReportPhoto({self.photo_id})>"