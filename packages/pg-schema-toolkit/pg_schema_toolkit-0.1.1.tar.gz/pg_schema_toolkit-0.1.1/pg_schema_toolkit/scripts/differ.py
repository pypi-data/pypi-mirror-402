"""
Schema Differ - Compare YAML schema with database state

This module compares YAML schema definitions with the actual database
structure and identifies what changes need to be made.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from pg_schema_toolkit.scripts.introspector import DatabaseIntrospector, TableInfo, ColumnInfo
from pg_schema_toolkit.scripts.schema_loader import LoadedSchema


class ChangeType(Enum):
    """Types of schema changes."""
    # Schema level
    CREATE_SCHEMA = "create_schema"
    
    # Table level
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    
    # Column level
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN_TYPE = "modify_column_type"
    MODIFY_COLUMN_NULLABLE = "modify_column_nullable"
    MODIFY_COLUMN_DEFAULT = "modify_column_default"
    
    # Index level
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    
    # Constraint level
    ADD_UNIQUE_CONSTRAINT = "add_unique_constraint"
    DROP_UNIQUE_CONSTRAINT = "drop_unique_constraint"
    
    # Audit infrastructure
    CREATE_AUDIT_TABLE = "create_audit_table"
    RECREATE_TRIGGER_FUNCTION = "recreate_trigger_function"


class SafetyLevel(Enum):
    """Safety classification for schema changes."""
    SAFE = "safe"              # No data risk, reversible
    WARNING = "warning"         # Needs attention, may require data work
    DESTRUCTIVE = "destructive" # Data loss possible


@dataclass
class SchemaChange:
    """
    Represents a single schema change.
    """
    change_type: ChangeType
    safety_level: SafetyLevel
    table_name: str
    description: str
    
    # For audit-aware changes
    affects_audit_table: bool = False
    affects_trigger: bool = False
    
    # Additional details
    details: Dict[str, Any] = None
    
    def __str__(self):
        icon = {
            SafetyLevel.SAFE: "✓",
            SafetyLevel.WARNING: "⚠",
            SafetyLevel.DESTRUCTIVE: "✗"
        }[self.safety_level]
        
        result = f"{icon} {self.description}"
        if self.affects_audit_table or self.affects_trigger:
            result += " [affects audit infrastructure]"
        return result


class SchemaDiffer:
    """
    Compare YAML schema definition with database state.
    
    Identifies all changes needed to make the database match the YAML definition.
    """
    
    def __init__(self, yaml_schema: LoadedSchema, introspector: DatabaseIntrospector):
        """
        Initialize differ.
        
        Args:
            yaml_schema: Loaded YAML schema definition
            introspector: Database introspector instance
        """
        self.yaml_schema = yaml_schema
        self.introspector = introspector
        self.schema_name = yaml_schema.schema_name
    
    def is_audited_table(self, table: Dict[str, Any]) -> bool:
        """Check if table has audit infrastructure."""
        return table.get('generate_audit_table', False)
    
    def get_audit_table_name(self, table_name: str) -> str:
        """Get audit table name for a given table."""
        if hasattr(self.yaml_schema, 'base_definitions') and self.yaml_schema.base_definitions:
            audit_config = self.yaml_schema.base_definitions.get('audit_config', {})
            suffix = audit_config.get('audit_table_suffix', '_audr')
            return f"{table_name}{suffix}"
        return f"{table_name}_audr"
    
    def compare_column_type(self, yaml_type: str, db_type: str) -> bool:
        """
        Compare column types (PostgreSQL type normalization).
        
        Args:
            yaml_type: Type from YAML
            db_type: Type from database
            
        Returns:
            True if types match (after normalization)
        """
        # Normalize types for comparison
        type_map = {
            'BIGSERIAL': 'BIGINT',
            'SERIAL': 'INTEGER',
            'INT': 'INTEGER',
            'BOOL': 'BOOLEAN',
            'TIMESTAMP WITH TIME ZONE': 'TIMESTAMP WITH TIME ZONE',
            'TIMESTAMP WITHOUT TIME ZONE': 'TIMESTAMP',
        }
        
        yaml_normalized = type_map.get(yaml_type.upper(), yaml_type.upper())
        db_normalized = type_map.get(db_type.upper(), db_type.upper())
        
        # DECIMAL and NUMERIC are aliases in PostgreSQL
        if yaml_normalized.startswith('DECIMAL'):
            yaml_normalized = yaml_normalized.replace('DECIMAL', 'NUMERIC')
        if db_normalized.startswith('DECIMAL'):
            db_normalized = db_normalized.replace('DECIMAL', 'NUMERIC')
        
        return yaml_normalized == db_normalized
    
    def classify_column_change_safety(self, change_type: ChangeType, 
                                       yaml_col: Dict[str, Any], 
                                       db_col: Optional[ColumnInfo]) -> SafetyLevel:
        """
        Classify the safety level of a column change.
        
        Args:
            change_type: Type of change
            yaml_col: Column from YAML (or None for drop)
            db_col: Column from DB (or None for add)
            
        Returns:
            SafetyLevel classification
        """
        if change_type == ChangeType.ADD_COLUMN:
            # Adding nullable column is safe
            if 'NOT NULL' not in yaml_col.get('constraints', ''):
                return SafetyLevel.SAFE
            # Adding NOT NULL with default is safe
            if 'default' in yaml_col:
                return SafetyLevel.SAFE
            # Adding NOT NULL without default is warning (need to handle existing rows)
            return SafetyLevel.WARNING
        
        elif change_type == ChangeType.DROP_COLUMN:
            # Dropping column is always destructive
            return SafetyLevel.DESTRUCTIVE
        
        elif change_type == ChangeType.MODIFY_COLUMN_TYPE:
            # Type changes can be risky
            return SafetyLevel.WARNING
        
        elif change_type == ChangeType.MODIFY_COLUMN_NULLABLE:
            # Making nullable is safe
            if yaml_col and 'NOT NULL' not in yaml_col.get('constraints', ''):
                return SafetyLevel.SAFE
            # Making NOT NULL is warning
            return SafetyLevel.WARNING
        
        elif change_type == ChangeType.MODIFY_COLUMN_DEFAULT:
            # Changing default is safe (only affects new rows)
            return SafetyLevel.SAFE
        
        return SafetyLevel.SAFE
    
    def compare_table(self, yaml_table: Dict[str, Any], 
                     db_table: Optional[TableInfo]) -> List[SchemaChange]:
        """
        Compare a single table between YAML and database.
        
        Args:
            yaml_table: Table definition from YAML
            db_table: Table info from database (or None if doesn't exist)
            
        Returns:
            List of SchemaChange objects
        """
        changes = []
        table_name = yaml_table['name']
        is_audited = self.is_audited_table(yaml_table)
        
        # Table doesn't exist - need to create it
        if db_table is None:
            changes.append(SchemaChange(
                change_type=ChangeType.CREATE_TABLE,
                safety_level=SafetyLevel.SAFE,
                table_name=table_name,
                description=f"Create table {table_name}",
                affects_audit_table=is_audited,
                affects_trigger=is_audited
            ))
            return changes
        
        # Table exists - compare columns
        yaml_columns = {col['name']: col for col in yaml_table['_expanded_columns']}
        db_columns = {col.name: col for col in db_table.columns}
        
        # Check for new columns
        for col_name, yaml_col in yaml_columns.items():
            if col_name not in db_columns:
                safety = self.classify_column_change_safety(
                    ChangeType.ADD_COLUMN, yaml_col, None
                )
                changes.append(SchemaChange(
                    change_type=ChangeType.ADD_COLUMN,
                    safety_level=safety,
                    table_name=table_name,
                    description=f"Add column {col_name} ({yaml_col['type']})",
                    affects_audit_table=is_audited,
                    affects_trigger=is_audited,
                    details={'column': yaml_col}
                ))
        
        # Note: We intentionally do NOT check for columns in DB but not in YAML.
        # DROP COLUMN operations should be done manually as they are destructive.
        
        # Check for modified columns
        for col_name in set(yaml_columns.keys()) & set(db_columns.keys()):
            yaml_col = yaml_columns[col_name]
            db_col = db_columns[col_name]
            
            # Type change
            db_full_type = db_col.get_full_type()
            if not self.compare_column_type(yaml_col['type'], db_full_type):
                changes.append(SchemaChange(
                    change_type=ChangeType.MODIFY_COLUMN_TYPE,
                    safety_level=SafetyLevel.WARNING,
                    table_name=table_name,
                    description=f"Change column {col_name} type: {db_full_type} → {yaml_col['type']}",
                    affects_audit_table=is_audited,
                    affects_trigger=False,  # Type change doesn't affect trigger
                    details={'column': yaml_col, 'old_type': db_full_type}
                ))
        
        # Check indexes
        changes.extend(self.compare_indexes(yaml_table, db_table))
        
        # If table is audited, check if audit infrastructure needs updates
        if is_audited and changes:
            # Any column change requires trigger recreation
            column_changes = [c for c in changes if c.change_type in [
                ChangeType.ADD_COLUMN, ChangeType.DROP_COLUMN, ChangeType.MODIFY_COLUMN_TYPE
            ]]
            if column_changes:
                changes.append(SchemaChange(
                    change_type=ChangeType.RECREATE_TRIGGER_FUNCTION,
                    safety_level=SafetyLevel.SAFE,
                    table_name=table_name,
                    description=f"Recreate trigger function (column changes detected)",
                    affects_trigger=True
                ))
        
        return changes
    
    def compare_indexes(self, yaml_table: Dict[str, Any], 
                       db_table: TableInfo) -> List[SchemaChange]:
        """
        Compare indexes between YAML and database.
        
        Args:
            yaml_table: Table from YAML
            db_table: Table from database
            
        Returns:
            List of index-related changes
        """
        changes = []
        table_name = yaml_table['name']
        
        # Get YAML indexes (excluding primary key indexes)
        yaml_indexes = {}
        for idx in yaml_table.get('_all_indexes', []):
            cols_key = tuple(sorted(idx['columns']))
            yaml_indexes[cols_key] = idx
        
        # Get DB indexes (excluding primary key and unique constraint indexes)
        db_indexes = {}
        for idx in db_table.indexes:
            if not idx.is_primary:
                cols_key = tuple(sorted(idx.columns))
                db_indexes[cols_key] = idx
        
        # Check for new indexes
        for cols_key, yaml_idx in yaml_indexes.items():
            if cols_key not in db_indexes:
                col_names = ", ".join(yaml_idx['columns'])
                changes.append(SchemaChange(
                    change_type=ChangeType.ADD_INDEX,
                    safety_level=SafetyLevel.SAFE,
                    table_name=table_name,
                    description=f"Add index on ({col_names})",
                    details={'index': yaml_idx}
                ))
        
        # Check for dropped indexes
        for cols_key, db_idx in db_indexes.items():
            if cols_key not in yaml_indexes:
                col_names = ", ".join(db_idx.columns)
                changes.append(SchemaChange(
                    change_type=ChangeType.DROP_INDEX,
                    safety_level=SafetyLevel.SAFE,
                    table_name=table_name,
                    description=f"Drop index {db_idx.name}",
                    details={'index_name': db_idx.name}
                ))
        
        return changes
    
    def compare_schemas(self) -> List[SchemaChange]:
        """
        Compare complete YAML schema with database.
        
        Returns:
            List of all changes needed
        """
        changes = []
        
        # Check if schema exists
        if not self.introspector.schema_exists(self.schema_name):
            changes.append(SchemaChange(
                change_type=ChangeType.CREATE_SCHEMA,
                safety_level=SafetyLevel.SAFE,
                table_name="",
                description=f"Create schema {self.schema_name}"
            ))
            # If schema doesn't exist, all tables need to be created
            for table in self.yaml_schema.tables:
                changes.append(SchemaChange(
                    change_type=ChangeType.CREATE_TABLE,
                    safety_level=SafetyLevel.SAFE,
                    table_name=table['name'],
                    description=f"Create table {table['name']}",
                    affects_audit_table=self.is_audited_table(table),
                    affects_trigger=self.is_audited_table(table)
                ))
            return changes
        
        # Schema exists - get current state
        db_tables = self.introspector.introspect_schema(self.schema_name)
        
        # Compare each table from YAML
        for yaml_table in self.yaml_schema.tables:
            table_name = yaml_table['name']
            db_table = db_tables.get(table_name)
            
            table_changes = self.compare_table(yaml_table, db_table)
            changes.extend(table_changes)
        
        # Check for dropped tables
        yaml_table_names = {t['name'] for t in self.yaml_schema.tables}
        # Note: We intentionally do NOT check for tables in DB but not in YAML.
        # This allows multi-file schema management where each YAML file defines
        # a subset of tables. DROP TABLE operations should be done manually.
        
        return changes
    
    def group_changes_by_safety(self, changes: List[SchemaChange]) -> Dict[SafetyLevel, List[SchemaChange]]:
        """
        Group changes by safety level.
        
        Args:
            changes: List of changes
            
        Returns:
            Dictionary mapping SafetyLevel to list of changes
        """
        grouped = {
            SafetyLevel.SAFE: [],
            SafetyLevel.WARNING: [],
            SafetyLevel.DESTRUCTIVE: []
        }
        
        for change in changes:
            grouped[change.safety_level].append(change)
        
        return grouped
