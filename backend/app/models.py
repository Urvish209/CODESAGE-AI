from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base


# ===========================
# USER TABLE
# ===========================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ===========================
# REVIEW TABLE
# ===========================

class Review(Base):
    __tablename__ = "reviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    repository = Column(
        String(255),
        nullable=False
    )

    files_analyzed = Column(
        Integer,
        default=0
    )

    security_score = Column(
        Integer,
        default=0
    )

    performance_score = Column(
        Integer,
        default=0
    )

    code_quality_score = Column(
        Integer,
        default=0
    )

    overall_score = Column(
        Integer,
        default=0
    )

    issues = Column(
        Text,
        nullable=True
    )

    suggestions = Column(
        Text,
        nullable=True
    )

    review_text = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )