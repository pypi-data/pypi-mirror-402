"""SQLAlchemy ORM models for memrun platform."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class ServiceModel(Base):
    """ORM model for services."""

    __tablename__ = "services"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    memory: Mapped[str] = mapped_column(String(20), nullable=False, default="4Gi")
    disk: Mapped[str] = mapped_column(String(20), nullable=False, default="100Gi")
    max_workers: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    min_workers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    sticky_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    env: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    url_id: Mapped[str | None] = mapped_column(String(6), nullable=True, unique=True)
    image: Mapped[str] = mapped_column(String(500), nullable=False, default="python:3.12-slim")
    current_deployment_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployments.id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    deployments: Mapped[list["DeploymentModel"]] = relationship(
        "DeploymentModel",
        back_populates="service",
        foreign_keys="DeploymentModel.service_id",
    )
    requests: Mapped[list["RequestModel"]] = relationship(
        "RequestModel",
        back_populates="service",
    )


class DeploymentModel(Base):
    """ORM model for deployments."""

    __tablename__ = "deployments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
    )
    image_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    artifact_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="S3 URL to deployment package tarball (e.g., s3://memrun-artifacts/deployments/{service}/{id}/package.tar.gz)",
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    service: Mapped["ServiceModel"] = relationship(
        "ServiceModel",
        back_populates="deployments",
        foreign_keys=[service_id],
    )

    __table_args__ = (
        Index("ix_deployments_service_id", "service_id"),
        Index("ix_deployments_status", "status"),
    )


class RequestModel(Base):
    """ORM model for requests."""

    __tablename__ = "requests"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
    )
    sticky_key_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    service: Mapped["ServiceModel"] = relationship(
        "ServiceModel",
        back_populates="requests",
    )

    __table_args__ = (
        Index("ix_requests_service_id", "service_id"),
        Index("ix_requests_status", "status"),
        Index("ix_requests_sticky_key", "service_id", "sticky_key_value"),
    )


class WorkerStatsModel(Base):
    """ORM model for worker heartbeats and stats."""

    __tablename__ = "worker_stats"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
    )
    worker_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Stats from ExecutorStats
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    active_requests: Mapped[int] = mapped_column(Integer, default=0)
    avg_duration_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Worker readiness status
    ready: Mapped[bool] = mapped_column(Boolean, default=False)

    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_worker_stats_service_worker", "service_id", "worker_id", unique=True),
        Index("ix_worker_stats_last_heartbeat", "last_heartbeat"),
    )
