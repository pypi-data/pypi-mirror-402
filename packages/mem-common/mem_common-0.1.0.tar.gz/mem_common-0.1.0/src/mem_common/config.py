"""Platform configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MEMRUN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Worker provisioning
    worker_provisioner: Literal["hetzner", "local"] = Field(
        default="hetzner",
        description="Worker provisioner type: 'hetzner' for cloud VMs, 'local' for Docker containers",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://memrun:memrun@localhost:5432/memrun",
        description="PostgreSQL connection URL",
    )

    # Kafka/Redpanda
    kafka_bootstrap_servers: str = Field(
        default="localhost:19092",
        description="Comma-separated list of Kafka broker addresses",
    )
    kafka_consumer_group_prefix: str = Field(
        default="memrun",
        description="Prefix for Kafka consumer groups",
    )

    # S3/MinIO
    s3_endpoint_url: str = Field(
        default="http://localhost:9000",
        description="S3-compatible endpoint URL",
    )
    s3_access_key_id: str = Field(
        default="minioadmin",
        description="S3 access key ID",
    )
    s3_secret_access_key: str = Field(
        default="minioadmin",
        description="S3 secret access key",
    )
    s3_bucket_artifacts: str = Field(
        default="memrun-artifacts",
        description="Bucket for deployment artifacts",
    )
    s3_bucket_cache: str = Field(
        default="memrun-cache",
        description="Bucket for cached data",
    )
    s3_bucket_registry: str = Field(
        default="memrun-registry",
        description="Bucket for container registry",
    )
    s3_region: str = Field(
        default="us-east-1",
        description="S3 region (for signature)",
    )
    s3_public_endpoint_url: str = Field(
        default="",
        description="Public S3 endpoint URL (for workers accessing from outside the cluster). Falls back to s3_endpoint_url if not set.",
    )

    # Hetzner Cloud
    hetzner_api_token: str = Field(
        default="",
        description="Hetzner Cloud API token",
    )
    hetzner_location: str = Field(
        default="ash",
        description="Default Hetzner datacenter location (ash=US, hil=US West)",
    )
    hetzner_network_id: int | None = Field(
        default=None,
        description="Hetzner private network ID for workers",
    )
    hetzner_dns_zone_id: str = Field(
        default="",
        description="DNS zone ID for memrun.net (auto-discovered if not set)",
    )
    api_server_ip: str = Field(
        default="",
        description="Public IP of API server for DNS records",
    )

    # API Server
    api_host: str = Field(
        default="0.0.0.0",
        description="API server bind host",
    )
    api_port: int = Field(
        default=8000,
        description="API server bind port",
    )
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="External API base URL",
    )

    # Worker defaults
    worker_image: str = Field(
        default="ghcr.io/jmulla/mem-worker:latest",
        description="Docker image for worker runtime",
    )
    github_token: str = Field(
        default="",
        description="GitHub personal access token for pulling private container images",
    )
    default_worker_memory: str = Field(
        default="4Gi",
        description="Default worker memory allocation",
    )
    default_worker_disk: str = Field(
        default="100Gi",
        description="Default worker disk allocation",
    )
    default_worker_concurrency: int = Field(
        default=16,
        description="Default concurrent requests per worker",
    )

    @property
    def kafka_brokers(self) -> list[str]:
        """Return Kafka brokers as a list."""
        return [b.strip() for b in self.kafka_bootstrap_servers.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
