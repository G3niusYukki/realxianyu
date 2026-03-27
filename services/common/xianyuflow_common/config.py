"""Configuration management using pydantic-settings."""

from __future__ import annotations

from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="xianyuflow", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: SecretStr = Field(default=SecretStr(""), description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Maximum pool overflow")

    @property
    def dsn(self) -> str:
        """Generate database DSN."""
        password = self.password.get_secret_value() if self.password else ""
        return f"postgresql+asyncpg://{self.user}:{password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[SecretStr] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")


class KafkaConfig(BaseSettings):
    """Kafka configuration."""

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)",
    )
    client_id: Optional[str] = Field(default=None, description="Kafka client ID")


class AIConfig(BaseSettings):
    """AI service configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="DeepSeek API key",
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API base URL",
    )
    default_model: str = Field(
        default="deepseek-chat",
        description="Default AI model",
    )
    max_context_messages: int = Field(
        default=20,
        description="Maximum context messages",
    )


class XianyuConfig(BaseSettings):
    """Xianyu API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="XIANYU_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_key: str = Field(default="", description="Xianyu app key")
    app_secret: SecretStr = Field(
        default=SecretStr(""),
        description="Xianyu app secret",
    )
    base_url: str = Field(
        default="https://api.xianyu.com",
        description="Xianyu API base URL",
    )


class ServiceConfig(BaseSettings):
    """Main service configuration containing all sub-configurations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="xianyuflow-service", description="Service name")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    log_level: str = Field(default="INFO", description="Log level")

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    xianyu: XianyuConfig = Field(default_factory=XianyuConfig)
