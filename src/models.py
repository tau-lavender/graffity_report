from datetime import datetime
from geoalchemy2 import Geography  # type: ignore[import-not-found]
from sqlalchemy import (  # type: ignore[import-not-found]
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore[import-not-found]
from sqlalchemy.orm import DeclarativeBase, relationship  # type: ignore[import-not-found]


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reports = relationship("GraffitiReport", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User({self.user_id})>"


class GraffitiReport(Base):
    __tablename__ = "graffiti_reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    fias_id = Column(UUID(as_uuid=True), nullable=True)
    normalized_address = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="reports")
    photos = relationship("ReportPhoto", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'declined')", name="check_status_values"),
    )

    def __repr__(self):
        return f"<GraffitiReport({self.report_id})>"


class ReportPhoto(Base):
    __tablename__ = "report_photos"

    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("graffiti_reports.report_id", ondelete="CASCADE"), nullable=False)
    s3_key = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("GraffitiReport", back_populates="photos")

    def __repr__(self):
        return f"<ReportPhoto({self.photo_id})>"
