"""
SQLAlchemy models for GraffitiReport application.
Supports PostGIS geography types for location data.
"""
from datetime import datetime
from geoalchemy2 import Geography  # type: ignore
from sqlalchemy import (  # type: ignore
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from sqlalchemy.orm import DeclarativeBase, relationship  # type: ignore


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """
    Telegram user model.
    Stores user_id (telegram ID), username, and additional profile data.
    """
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, comment="Telegram user ID")
    username = Column(String(255), nullable=True, comment="Telegram username (without @)")
    first_name = Column(String(255), nullable=True, comment="Telegram first name")
    last_name = Column(String(255), nullable=True, comment="Telegram last name")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    reports = relationship("GraffitiReport", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class GraffitiReport(Base):
    """
    Graffiti report submitted by user.
    Includes location (PostGIS geography), address, status, description, and photos.
    """
    __tablename__ = "graffiti_reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="Telegram user who submitted the report (nullable)"
    )
    location = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment="Geolocation (latitude, longitude) in WGS84"
    )
    fias_id = Column(UUID(as_uuid=True), nullable=True, comment="FIAS address ID from DaData")
    normalized_address = Column(Text, nullable=True, comment="Normalized address from DaData or manual input")
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="Report status: pending, approved, declined"
    )
    description = Column(Text, nullable=True, comment="User comment about graffiti")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")
    photos = relationship("ReportPhoto", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'declined')",
            name="check_status_values"
        ),
    )

    def __repr__(self):
        return f"<GraffitiReport(report_id={self.report_id}, status={self.status})>"


class ReportPhoto(Base):
    """
    Photo attached to a graffiti report.
    s3_key is the object key in MinIO/S3 bucket.
    """
    __tablename__ = "report_photos"

    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("graffiti_reports.report_id", ondelete="CASCADE"),
        nullable=False
    )
    s3_key = Column(String(255), nullable=False, comment="S3/MinIO object key")
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("GraffitiReport", back_populates="photos")

    def __repr__(self):
        return f"<ReportPhoto(photo_id={self.photo_id}, s3_key={self.s3_key})>"
