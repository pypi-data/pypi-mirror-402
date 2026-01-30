"""Service and configuration models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceStatus(StrEnum):
    """Status of a deployed service."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    SCALING = "scaling"
    STOPPED = "stopped"
    FAILED = "failed"


class ServiceConfig(BaseModel):
    """Configuration for a service deployment."""

    memory: str = Field(
        default="4Gi",
        description="Memory allocation (e.g., '32Gi')",
        pattern=r"^\d+[KMGT]i$",
    )
    disk: str = Field(
        default="100Gi",
        description="Disk allocation for NVMe cache (e.g., '600Gi')",
        pattern=r"^\d+[KMGT]i$",
    )
    max_workers: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum number of worker instances",
    )
    min_workers: int = Field(
        default=0,
        ge=0,
        description="Minimum number of worker instances (0 for scale-to-zero)",
    )
    concurrency: int = Field(
        default=16,
        ge=1,
        le=1000,
        description="Concurrent requests per worker",
    )
    sticky_key: str | None = Field(
        default=None,
        description="Request field for sticky routing (e.g., 'user_id:dataset_id')",
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Request timeout in seconds",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for worker containers",
    )

    def memory_bytes(self) -> int:
        """Convert memory string to bytes."""
        return self._parse_size(self.memory)

    def disk_bytes(self) -> int:
        """Convert disk string to bytes."""
        return self._parse_size(self.disk)

    @staticmethod
    def _parse_size(size: str) -> int:
        """Parse size string like '32Gi' to bytes."""
        units = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4}
        for suffix, multiplier in units.items():
            if size.endswith(suffix):
                return int(size[: -len(suffix)]) * multiplier
        return int(size)


class Service(BaseModel):
    """A deployed service on the memrun platform."""

    id: UUID
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$",
        description="Service name (DNS-compatible)",
    )
    image: str = Field(..., description="Docker image URI")
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.PENDING
    current_workers: int = Field(default=0, ge=0)
    current_deployment_id: UUID | None = None
    url_id: str | None = Field(default=None, description="6-character unique URL identifier")
    url: str | None = Field(default=None, description="Service endpoint URL")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeploymentStatus(StrEnum):
    """Status of a deployment."""

    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Deployment(BaseModel):
    """A deployment version for a service."""

    id: UUID
    service_id: UUID
    image_uri: str = Field(..., description="Container image URI")
    status: DeploymentStatus = DeploymentStatus.PENDING
    error_message: str | None = None
    created_at: datetime
    deployed_at: datetime | None = None

    model_config = {"from_attributes": True}


class Worker(BaseModel):
    """A worker instance running a service."""

    id: UUID
    service_id: UUID
    deployment_id: UUID
    hetzner_server_id: int | None = None
    ip_address: str | None = None
    status: str = "provisioning"
    created_at: datetime
    ready_at: datetime | None = None

    model_config = {"from_attributes": True}
