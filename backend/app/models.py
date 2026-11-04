from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220))
    destination: Mapped[str] = mapped_column(String(120))
    duration_days: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    hero_image: Mapped[str] = mapped_column(String(500), default="")
    itinerary: Mapped[list] = mapped_column(JSON, default=list)
    inclusions: Mapped[list] = mapped_column(JSON, default=list)
    hotel_category: Mapped[str] = mapped_column(String(80), default="4 star")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    published_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    seasons: Mapped[list["SeasonPrice"]] = relationship(back_populates="package", cascade="all, delete-orphan")
    versions: Mapped[list["PackageVersion"]] = relationship(back_populates="package", cascade="all, delete-orphan")

class SeasonPrice(Base):
    __tablename__ = "season_prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"))
    season: Mapped[str] = mapped_column(String(80))
    start_month: Mapped[int] = mapped_column(Integer)
    end_month: Mapped[int] = mapped_column(Integer)
    price_per_person: Mapped[float] = mapped_column(Numeric(10, 2))
    basis: Mapped[str] = mapped_column(String(120), default="per person, twin sharing")
    gst_note: Mapped[str] = mapped_column(String(120), default="GST extra as applicable")
    package: Mapped[Package] = relationship(back_populates="seasons")

class PackageVersion(Base):
    __tablename__ = "package_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    package: Mapped[Package] = relationship(back_populates="versions")

class Enquiry(Base):
    __tablename__ = "enquiries"
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int | None] = mapped_column(ForeignKey("packages.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(40), default="")
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="website")
    status: Mapped[str] = mapped_column(String(30), default="new")
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    extracted: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_suggestions: Mapped[list] = mapped_column(JSON, default=list)
    ai_draft: Mapped[str] = mapped_column(Text, default="")
    whatsapp_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
