# pg-schema-toolkit

A self-contained PostgreSQL schema management toolkit with YAML-based definitions, automatic audit tables, and intelligent schema change tracking.

**Philosophy:** Schema-first design. Define your database structure in YAML, generate clean DDL, track changes, and maintain complete audit trails.

---

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Optional: Install with tab completion support
pip install -e ".[completion]"
activate-global-python-argcomplete --user
# Then restart your shell or source ~/.bashrc

# Validate a schema
pg-schema validate examples/schemas/users.yaml

# Generate DDL
pg-schema generate examples/schemas/users.yaml -o create_users.sql

# Compare YAML with database
pg-schema diff examples/schemas/users.yaml

# Generate schema change SQL
pg-schema generate-change examples/schemas/users.yaml \
    -m "Add status column" \
    -o schema_changes/002_add_status.sql

# Apply change to database
psql < schema_changes/002_add_status.sql
```

---

## 📦 Core Features

- ✅ **YAML Schema Definitions** - Define tables declaratively
- ✅ **Schema Inheritance** - Reusable templates and field types
- ✅ **DDL Generation** - Generate clean `CREATE TABLE` statements
- ✅ **Automatic Audit Tables** - Track all changes with triggers
- ✅ **Database Introspection** - Read current database schema
- ✅ **Schema Diffing** - Compare YAML vs. database state
- ✅ **Change Generation** - Generate `ALTER TABLE` statements
- ✅ **Safety Classification** - SAFE/WARNING/DESTRUCTIVE labels
- ✅ **CLI Interface** - Complete command-line tooling

---

## 🔄 Schema Change Workflow

### Philosophy: Generate-First with Optional Execution

**Core Principle:** All schema changes are SQL files. Never execute DDL without a reviewed file.

### Complete Workflow

**1. Modify YAML Schema**
```yaml
# examples/schemas/users.yaml
tables:
  - name: users
    columns:
      - name: status
        type: TEXT
        default: "'active'"
```

**2. Generate Change File**
```bash
pg-schema generate-change examples/schemas/users.yaml \
  -m "Add status column" \
  -o schema_changes/005_add_status.sql
```

**3. Review Generated SQL**
```bash
cat schema_changes/005_add_status.sql
```

**4. Apply Change**
```bash
# Manual (recommended for production)
psql < schema_changes/005_add_status.sql
```

### Safety Classification

**SAFE** ✓
- Add nullable column
- Add index
- Add column with default

**WARNING** ⚠
- Add NOT NULL column
- Change column type
- Type conversions

**DESTRUCTIVE** ✗
- Drop column
- Drop table
- Data loss possible

---

## 🏗️ Example Schema

```yaml
# examples/schemas/users.yaml
schema: public
extends: base_definitions.yaml
description: "User accounts with full audit history"

tables:
  - name: users
    extends: audited_table  # Gets audit fields + audit table + trigger
    description: "Application users"
    
    columns:
      - name: email
        field_type: email
        description: "User email address"
      
      - name: username
        field_type: slug
        description: "Unique username"
      
      - name: full_name
        field_type: name
        description: "User's full name"
      
      - name: is_active
        field_type: is_active
        description: "Account active status"
    
    indexes:
      - columns: [email]
      - columns: [username]
      - columns: [is_active]
        where: "deleted_at IS NULL"
```

**Generates:**
- `public.users` table with audit fields
- `public.users_audr` audit table
- `audit_users()` trigger function
- `audit_users_trigger` trigger
- All indexes and constraints

---

## 🔧 Configuration

Uses standard PostgreSQL environment variables:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=mydb
export PGUSER=myuser
# Password from ~/.pgpass (secure)
```

Optional:
```bash
export DB_SCHEMA=public              # Default schema
export DB_CONNECT_TIMEOUT=10         # Connection timeout (seconds)
export ENVIRONMENT=development       # Environment name
```

---

## 🎯 Usage Patterns

### 1. As Command-Line Tool

```bash
# Validate schema
pg-schema validate examples/schemas/users.yaml

# Generate DDL
pg-schema generate examples/schemas/users.yaml -o /tmp/create_users.sql

# Apply to database
psql -f /tmp/create_users.sql
```

### 2. As Python Library

```python
from pg_schema_toolkit import SchemaLoader, DDLGenerator, load_config_from_env
import psycopg2

# Load schema
loader = SchemaLoader()
schema = loader.load_schema('examples/schemas/users.yaml')

# Generate DDL
generator = DDLGenerator(schema)
ddl = generator.generate_all()

# Connect to database
config = load_config_from_env()
conn = psycopg2.connect(**config.psycopg2_params)
```

---

## 📂 Project Structure

```
pg-schema-toolkit/
├── pg_schema_toolkit/          # Main package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   └── scripts/                # Core functionality
│       ├── schema_loader.py    # Load and parse YAML
│       ├── ddl_generator.py    # Generate CREATE TABLE
│       ├── audit_generator.py  # Generate audit infrastructure
│       ├── introspector.py     # Read database schema
│       ├── differ.py           # Compare YAML vs database
│       ├── change_generator.py # Generate ALTER TABLE
│       └── db_config.py        # Database connection
├── examples/
│   └── schemas/                # Example schemas
│       ├── base_definitions.yaml
│       ├── users.yaml
│       └── products.yaml
├── pyproject.toml              # Package configuration
├── setup.py                    # Setup script
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

---

## 🔍 Audit Table System

Every table marked with `generate_audit_table: true` automatically gets:

- `{table_name}_audr` audit table
- Trigger function to capture INSERT/UPDATE/DELETE
- Complete change history with timestamps, users, and operation types
- Indexes on `audit_row_id`, `audit_timestamp`, `audit_operation`, `audit_user`

### Example

```sql
-- Main table
INSERT INTO users (email, username) VALUES ('user@example.com', 'john');

-- Audit table automatically populated
SELECT * FROM users_audr;
-- audit_id | audit_timestamp | audit_user | audit_operation | audit_row_id | email | username
-- 1        | 2026-01-17...   | myuser     | INSERT          | 1            | user@... | john

-- Update tracked
UPDATE users SET username = 'john_doe' WHERE id = 1;

SELECT * FROM users_audr ORDER BY audit_id;
-- Shows both INSERT and UPDATE operations with full snapshots
```

---

## 📚 Best Practices

### Schema Changes

1. **Small, Incremental Changes**
   - Prefer many small changes over one large change

2. **Always Use Transactions**
   - Wrap related changes in `BEGIN`/`COMMIT`

3. **Test in Staging First**
   - Never apply untested changes to production

4. **Backwards Compatibility**
   - Add nullable column first
   - Backfill data
   - Then make NOT NULL

5. **Version Control**
   ```bash
   git add schema_changes/005_add_field.sql
   git commit -m "Schema change: add status field"
   ```

### Development Workflow

1. **Edit YAML schema** - Make changes declaratively
2. **Generate change** - Tool creates SQL file
3. **Review SQL** - Always review before applying
4. **Test locally** - Apply to dev database
5. **Commit SQL file** - Track in git
6. **Apply to staging** - Test in staging environment
7. **Apply to production** - Manual execution recommended

---

## 🚦 Status

**Production Ready** ✅

- Comprehensive feature set
- Clean, maintainable code
- Schema-first design philosophy
- Safe for production use

---

## 📖 CLI Reference

```bash
# Validate schema
pg-schema validate <schema_file>

# Generate DDL
pg-schema generate <schema_file> [-o output.sql]

# Show database info
pg-schema info

# Compare with database
pg-schema diff <schema_file>

# Generate change file
pg-schema generate-change <schema_file> -m "message" [-o output.sql]
```

---

## 🎓 Why Schema-First?

**Data Integrity = Business Rules**
- Constraints enforced at DB level, not app level
- Single source of truth
- Multi-client safety
- Audit from day one

**For ERP Systems:**
- Financial/regulatory data needs complete history
- Can't retrofit audit tables later
- Database enforces rules even with multiple apps
- Future integrations are safe

---

## 📄 License

MIT License

---

**Questions? Check the examples!** The `examples/schemas/` directory contains working examples of every feature.
