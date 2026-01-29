"""
PostgreSQL Schema Toolkit - YAML-based schema management for PostgreSQL.

This package provides tools for:
- Defining database schemas in YAML
- Generating DDL statements
- Creating audit tables automatically
- Tracking schema changes
- Comparing schemas with database state
- Generating migration scripts
"""

__version__ = "1.0.0"

from pg_schema_toolkit.scripts.schema_loader import SchemaLoader
from pg_schema_toolkit.scripts.ddl_generator import DDLGenerator
from pg_schema_toolkit.scripts.audit_generator import AuditTableGenerator
from pg_schema_toolkit.scripts.db_config import load_config_from_env, DatabaseConfig

__all__ = [
    "SchemaLoader",
    "DDLGenerator",
    "AuditTableGenerator",
    "load_config_from_env",
    "DatabaseConfig",
]
