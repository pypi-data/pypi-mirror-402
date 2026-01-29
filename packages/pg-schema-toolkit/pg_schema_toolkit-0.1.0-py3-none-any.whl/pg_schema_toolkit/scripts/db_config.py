"""
Database configuration from environment variables.

This module provides database connection configuration using explicit
environment variables with NO fallbacks (per project standards).
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    host: str
    port: int
    name: str
    user: str
    password: Optional[str]  # Can be None if using .pgpass
    schema: str
    connect_timeout: int
    environment: str
    
    @property
    def connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        if self.password:
            return (
                f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        else:
            # Use .pgpass authentication (secure!)
            return (
                f"postgresql://{self.user}"
                f"@{self.host}:{self.port}/{self.name}"
            )
    
    @property
    def psycopg2_params(self) -> dict:
        """Get psycopg2 connection parameters."""
        params = {
            'host': self.host,
            'port': self.port,
            'database': self.name,
            'user': self.user,
            'connect_timeout': self.connect_timeout,
        }
        
        # Only add password if explicitly provided
        # Otherwise psycopg2 will use .pgpass
        if self.password:
            params['password'] = self.password
        
        return params
    
    def validate(self) -> None:
        """Validate configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
        
        if not self.name:
            raise ValueError("Database name cannot be empty")
        
        if not self.user:
            raise ValueError("Database user cannot be empty")
        
        print(f"Database Configuration:")
        print(f"  Environment: {self.environment}")
        print(f"  Host: {self.host}:{self.port}")
        print(f"  Database: {self.name}")
        print(f"  User: {self.user}")
        print(f"  Schema: {self.schema}")
        print(f"  Auth: {'password' if self.password else '.pgpass'}")


def load_config_from_env() -> DatabaseConfig:
    """
    Load database configuration from environment variables.
    
    Uses standard PostgreSQL environment variables for compatibility with psql.
    
    Required environment variables:
    - PGHOST
    - PGPORT
    - PGDATABASE
    - PGUSER
    
    Optional environment variables:
    - PGPASSWORD (if not using .pgpass)
    - DB_SCHEMA (defaults to 'public')
    - DB_CONNECT_TIMEOUT (defaults to 10 seconds)
    - ENVIRONMENT (defaults to 'development')
    
    Raises:
        ValueError: If required environment variables are missing.
    """
    
    # Helper function to get required env var
    def require_env(key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                f"Database configuration must be explicitly provided."
            )
        return value
    
    # Load configuration using PostgreSQL standard variables
    config = DatabaseConfig(
        host=require_env('PGHOST'),
        port=int(require_env('PGPORT')),
        name=require_env('PGDATABASE'),
        user=require_env('PGUSER'),
        password=os.getenv('PGPASSWORD'),  # Optional - can use .pgpass
        schema=os.getenv('DB_SCHEMA', 'public'),
        connect_timeout=int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
        environment=os.getenv('ENVIRONMENT', 'development'),
    )
    
    return config


# Module-level config (loaded on import if env vars are set)
_config: Optional[DatabaseConfig] = None


def get_config() -> DatabaseConfig:
    """
    Get database configuration.
    
    Loads from environment variables on first call, then caches.
    
    Returns:
        DatabaseConfig: Database configuration.
        
    Raises:
        ValueError: If required environment variables are not set.
    """
    global _config
    
    if _config is None:
        _config = load_config_from_env()
    
    return _config


def set_config(config: DatabaseConfig) -> None:
    """
    Set database configuration (for testing).
    
    Args:
        config: DatabaseConfig instance.
    """
    global _config
    _config = config


def reset_config() -> None:
    """Reset cached configuration (for testing)."""
    global _config
    _config = None

