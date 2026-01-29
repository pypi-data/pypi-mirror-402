# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-17

### Added
- Initial release of pg-schema-toolkit
- YAML-based PostgreSQL schema definitions
- Schema inheritance support (templates, field types, column patterns)
- DDL generation from YAML schemas
- Automatic audit table generation with triggers
- Database introspection (read current schema from PostgreSQL)
- Schema diffing (compare YAML with database state)
- Schema change generation (ALTER TABLE statements)
- Safety classification for changes (SAFE/WARNING/DESTRUCTIVE)
- CLI interface with commands: validate, generate, info, diff, generate-change
- Optional argcomplete support for tab completion
- Example schemas (users, products with base definitions)
- Comprehensive documentation

### Features
- Reusable column patterns (audit fields, basic entity fields)
- Reusable field types (email, slug, name, description, etc.)
- Audit table configuration with customizable naming
- Change history preservation in audit tables
- PostgreSQL environment variable support (PGHOST, PGPORT, etc.)
- Clean DDL generation with comments and proper formatting

[0.1.0]: https://github.com/fuchangyin/pg-schema-toolkit/releases/tag/v0.1.0
