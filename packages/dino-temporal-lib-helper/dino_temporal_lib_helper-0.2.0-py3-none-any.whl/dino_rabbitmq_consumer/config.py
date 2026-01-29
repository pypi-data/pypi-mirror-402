#!/usr/bin/env python3
"""
Configuration management for RabbitMQ Consumer
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from urllib.parse import quote


@dataclass
class RabbitMQConfig:
    """RabbitMQ connection and queue configuration"""
    exchange_name: str = field(default_factory=lambda: os.getenv("RABBITMQ_EXCHANGE_NAME", "ai_audio_exchange"))
    queue_name: str = field(default_factory=lambda: os.getenv("RABBITMQ_QUEUE_NAME", "ai_audio_queue"))
    routing_key: str = field(default_factory=lambda: os.getenv("RABBITMQ_ROUTING_KEY", "audio.process"))
    host: str = field(default_factory=lambda: os.getenv("RABBITMQ_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_PORT", "5672")))
    username: str = field(default_factory=lambda: os.getenv("RABBITMQ_USERNAME", "guest"))
    password: str = field(default_factory=lambda: os.getenv("RABBITMQ_PASSWORD", "guest"))
    heartbeat: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_HEARTBEAT", "60")))
    connection_timeout: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_CONNECTION_TIMEOUT", "10")))
    prefetch_count: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_PREFETCH_COUNT", "10")))

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.exchange_name:
            raise ValueError("RabbitMQ exchange name cannot be empty")
        if not self.queue_name:
            raise ValueError("RabbitMQ queue name cannot be empty")
        if not self.host:
            raise ValueError("RabbitMQ host cannot be empty")
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"RabbitMQ port must be between 1 and 65535, got {self.port}")
        if self.heartbeat < 0:
            raise ValueError(f"RabbitMQ heartbeat must be non-negative, got {self.heartbeat}")
        if self.connection_timeout <= 0:
            raise ValueError(f"RabbitMQ connection timeout must be positive, got {self.connection_timeout}")
        if self.prefetch_count <= 0:
            raise ValueError(f"RabbitMQ prefetch count must be positive, got {self.prefetch_count}")


@dataclass
class ConsumerConfig:
    """Consumer-specific configuration"""
    dead_letter_queue: str = field(default_factory=lambda: os.getenv("CONSUMER_DEAD_LETTER_QUEUE", "ai_audio_dlq"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("CONSUMER_MAX_RETRIES", "3")))
    retry_delay: int = field(default_factory=lambda: int(os.getenv("CONSUMER_RETRY_DELAY", "5")))

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.dead_letter_queue:
            raise ValueError("Dead letter queue name cannot be empty")
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {self.max_retries}")
        if self.retry_delay < 0:
            raise ValueError(f"Retry delay must be non-negative, got {self.retry_delay}")


class Config:
    """Main configuration class that aggregates all configuration sections"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        self.rabbitmq = RabbitMQConfig()
        self.consumer = ConsumerConfig()

        # Environment-specific settings
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format (for backward compatibility)"""
        return {
            "rabbitmq": {
                "exchange_name": self.rabbitmq.exchange_name,
                "queue_name": self.rabbitmq.queue_name,
                "routing_key": self.rabbitmq.routing_key,
                "host": self.rabbitmq.host,
                "port": self.rabbitmq.port,
                "username": self.rabbitmq.username,
                "password": self.rabbitmq.password,
                "heartbeat": self.rabbitmq.heartbeat,
                "connection_timeout": self.rabbitmq.connection_timeout,
                "prefetch_count": self.rabbitmq.prefetch_count,
            },
            "consumer": {
                "dead_letter_queue": self.consumer.dead_letter_queue,
                "max_retries": self.consumer.max_retries,
                "retry_delay": self.consumer.retry_delay,
            },
            "environment": self.environment,
            "log_level": self.log_level,
            "debug": self.debug,
        }

    def get_rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL with proper URL encoding"""
        username = quote(self.rabbitmq.username, safe='')
        password = quote(self.rabbitmq.password, safe='')
        return f"amqp://{username}:{password}@{self.rabbitmq.host}:{self.rabbitmq.port}/"

    def validate(self) -> bool:
        """Validate the entire configuration"""
        try:
            # Validation is done in __post_init__ methods of dataclasses
            # This method can be extended for cross-section validation
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")

    def __repr__(self) -> str:
        """String representation with masked sensitive data"""
        config_dict = self.to_dict()
        # Mask sensitive information
        config_dict["rabbitmq"]["password"] = "***"
        return f"Config({config_dict})"


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Dict[str, Any]:
    """
    Get configuration as dictionary (for backward compatibility)

    Returns:
        Dict containing all configuration settings
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate()

    return _config_instance.to_dict()


def get_config_instance() -> Config:
    """
    Get the configuration instance

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate()

    return _config_instance


def get_rabbitmq_url() -> str:
    """
    Get RabbitMQ connection URL

    Returns:
        RabbitMQ connection URL string
    """
    return get_config_instance().get_rabbitmq_url()


def reload_config() -> Config:
    """
    Reload configuration from environment variables

    Returns:
        New Config instance
    """
    global _config_instance
    _config_instance = Config()
    _config_instance.validate()
    return _config_instance


# For backward compatibility
def create_config_from_dict(config_dict: Dict[str, Any]) -> Config:
    """
    Create a Config instance from a dictionary (for testing or manual configuration)

    Args:
        config_dict: Dictionary containing configuration values

    Returns:
        Config instance
    """
    # Temporarily set environment variables
    original_env = {}

    try:
        # Map dictionary values to environment variables
        if "rabbitmq" in config_dict:
            rabbitmq = config_dict["rabbitmq"]
            env_mappings = {
                "RABBITMQ_EXCHANGE_NAME": rabbitmq.get("exchange_name"),
                "RABBITMQ_QUEUE_NAME": rabbitmq.get("queue_name"),
                "RABBITMQ_ROUTING_KEY": rabbitmq.get("routing_key"),
                "RABBITMQ_HOST": rabbitmq.get("host"),
                "RABBITMQ_PORT": str(rabbitmq.get("port", 5672)),
                "RABBITMQ_USERNAME": rabbitmq.get("username"),
                "RABBITMQ_PASSWORD": rabbitmq.get("password"),
                "RABBITMQ_HEARTBEAT": str(rabbitmq.get("heartbeat", 60)),
                "RABBITMQ_CONNECTION_TIMEOUT": str(rabbitmq.get("connection_timeout", 10)),
                "RABBITMQ_PREFETCH_COUNT": str(rabbitmq.get("prefetch_count", 10)),
            }

            for env_var, value in env_mappings.items():
                if value is not None:
                    original_env[env_var] = os.getenv(env_var)
                    os.environ[env_var] = str(value)

        # Create and return config instance
        config = Config()
        config.validate()
        return config

    finally:
        # Restore original environment variables
        for env_var, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value
