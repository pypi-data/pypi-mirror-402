"""
Schema Change Generator - Generate ALTER statements

This module generates SQL ALTER statements from SchemaChange objects,
handling both regular tables and audited tables with trigger updates.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from pg_schema_toolkit.scripts.differ import SchemaChange, ChangeType, SafetyLevel
from pg_schema_toolkit.scripts.audit_generator import AuditTableGenerator
from pg_schema_toolkit.scripts.schema_loader import LoadedSchema


def clean_sql(sql: str) -> str:
    """
    Remove trailing whitespace from SQL.

    Args:
        sql: SQL string

    Returns:
        SQL with trailing whitespace removed from each line
    """
    lines = sql.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    return '\n'.join(cleaned_lines)


class ChangeGenerator:
    """
    Generate SQL ALTER statements from schema changes.
    
    Handles:
    - Regular table changes
    - Audited table changes (main + audit + trigger)
    - Index changes
    - Constraint changes
    """
    
    def __init__(self, schema: LoadedSchema):
        """
        Initialize generator.
        
        Args:
            schema: Loaded YAML schema
        """
        self.schema = schema
        self.schema_name = schema.schema_name
        
        # Initialize audit generator if audit_config exists
        self.audit_generator: Optional[AuditTableGenerator] = None
        if hasattr(schema, 'base_definitions') and schema.base_definitions:
            audit_config = schema.base_definitions.get('audit_config')
            if audit_config:
                self.audit_generator = AuditTableGenerator(audit_config)
    
    def get_table_definition(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table definition from schema."""
        for table in self.schema.tables:
            if table['name'] == table_name:
                return table
        return None
    
    def generate_alter_add_column(self, change: SchemaChange) -> str:
        """
        Generate ALTER TABLE ADD COLUMN statement.
        
        Args:
            change: SchemaChange object
            
        Returns:
            SQL statement
        """
        table_name = f"{self.schema_name}.{change.table_name}"
        col = change.details['column']
        
        parts = [f"ALTER TABLE {table_name}"]
        parts.append(f"    ADD COLUMN {col['name']} {col['type']}")
        
        # Default
        if 'default' in col:
            default_val = col['default']
            # For JSONB columns, ensure type casting is applied
            if col['type'].upper() == 'JSONB' and '::jsonb' not in default_val.lower():
                # Ensure JSON values are quoted (unless already a string literal or function)
                if not (default_val.startswith("'") or default_val.upper().startswith(('NULL', 'CURRENT_'))):
                    default_val = f"'{default_val}'"
                default_val = f"{default_val}::jsonb"
            parts.append(f" DEFAULT {default_val}")
        
        # Constraints
        if 'constraints' in col:
            parts.append(f" {col['constraints']}")

        return clean_sql("".join(parts) + ";")
    
    def generate_alter_drop_column(self, change: SchemaChange) -> str:
        """Generate ALTER TABLE DROP COLUMN statement."""
        table_name = f"{self.schema_name}.{change.table_name}"
        col_name = change.details['column_name']

        return clean_sql(f"ALTER TABLE {table_name}\n    DROP COLUMN {col_name};")
    
    def generate_alter_column_type(self, change: SchemaChange) -> str:
        """Generate ALTER TABLE ALTER COLUMN TYPE statement."""
        table_name = f"{self.schema_name}.{change.table_name}"
        col = change.details['column']

        return clean_sql(f"ALTER TABLE {table_name}\n"
                        f"    ALTER COLUMN {col['name']} TYPE {col['type']};")
    
    def generate_create_index(self, change: SchemaChange) -> str:
        """Generate CREATE INDEX statement."""
        table_name = f"{self.schema_name}.{change.table_name}"
        idx = change.details['index']
        
        cols = ", ".join(idx['columns'])
        col_names = "_".join(idx['columns'])
        idx_name = f"idx_{change.table_name}_{col_names}"
        
        sql = f"CREATE INDEX {idx_name}\n    ON {table_name}({cols})"

        if 'where' in idx:
            sql += f"\n    WHERE {idx['where']}"

        return clean_sql(sql + ";")
    
    def generate_drop_index(self, change: SchemaChange) -> str:
        """Generate DROP INDEX statement."""
        idx_name = change.details['index_name']
        return clean_sql(f"DROP INDEX IF EXISTS {self.schema_name}.{idx_name};")
    
    def generate_change_sql(self, change: SchemaChange) -> str:
        """
        Generate SQL for a single change.
        
        Args:
            change: SchemaChange object
            
        Returns:
            SQL statement(s)
        """
        if change.change_type == ChangeType.CREATE_SCHEMA:
            return f"CREATE SCHEMA IF NOT EXISTS {self.schema_name};"
        
        elif change.change_type == ChangeType.CREATE_TABLE:
            # This shouldn't happen in schema changes (use generate command)
            return f"-- Table {change.table_name} needs to be created (use generate command)"
        
        elif change.change_type == ChangeType.ADD_COLUMN:
            return self.generate_alter_add_column(change)
        
        elif change.change_type == ChangeType.DROP_COLUMN:
            return self.generate_alter_drop_column(change)
        
        elif change.change_type == ChangeType.MODIFY_COLUMN_TYPE:
            return self.generate_alter_column_type(change)
        
        elif change.change_type == ChangeType.ADD_INDEX:
            return self.generate_create_index(change)
        
        elif change.change_type == ChangeType.DROP_INDEX:
            return self.generate_drop_index(change)
        
        elif change.change_type == ChangeType.RECREATE_TRIGGER_FUNCTION:
            # Handled separately in audit infrastructure section
            return None
        
        else:
            return f"-- TODO: {change.change_type.value} for {change.table_name}"
    
    def generate_audit_table_changes(self, table_name: str, 
                                     main_table_changes: List[SchemaChange]) -> List[str]:
        """
        Generate changes for audit table when main table changes.
        
        Args:
            table_name: Main table name
            main_table_changes: Changes to main table
            
        Returns:
            List of SQL statements for audit table
        """
        if not self.audit_generator:
            return []
        
        audit_table_name = self.audit_generator.get_audit_table_name(table_name)
        statements = []
        
        # For each column change in main table, apply to audit table
        for change in main_table_changes:
            if change.change_type == ChangeType.ADD_COLUMN:
                col = change.details['column']
                # Add to audit table without constraints (audit stores snapshots)
                statements.append(
                    f"ALTER TABLE {self.schema_name}.{audit_table_name}\n"
                    f"    ADD COLUMN {col['name']} {col['type']};"
                )
            
            elif change.change_type == ChangeType.MODIFY_COLUMN_TYPE:
                col = change.details['column']
                statements.append(
                    f"ALTER TABLE {self.schema_name}.{audit_table_name}\n"
                    f"    ALTER COLUMN {col['name']} TYPE {col['type']};"
                )
            
            elif change.change_type == ChangeType.DROP_COLUMN:
                # DO NOT drop from audit table - preserve history
                col_name = change.details['column_name']
                statements.append(
                    f"-- Column {col_name} NOT dropped from audit table (preserving history)"
                )
        
        return statements
    
    def generate_trigger_recreation(self, table_name: str) -> str:
        """
        Generate SQL to recreate trigger function.
        
        Args:
            table_name: Table name
            
        Returns:
            CREATE OR REPLACE FUNCTION statement
        """
        if not self.audit_generator:
            return ""
        
        # Get current table definition
        table_def = self.get_table_definition(table_name)
        if not table_def:
            return ""
        
        return self.audit_generator.generate_trigger_function(
            self.schema_name,
            table_name,
            table_def['_expanded_columns']
        )
    
    def generate_schema_change_file(self, changes: List[SchemaChange], 
                                    message: str) -> str:
        """
        Generate complete schema change SQL file.
        
        Args:
            changes: List of changes
            message: Description of changes
            
        Returns:
            Complete SQL file content
        """
        lines = []
        
        # Header
        lines.append("-- " + "=" * 70)
        lines.append(f"-- Schema Change: {message}")
        lines.append(f"-- Schema: {self.schema_name}")
        lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"-- Changes: {len(changes)}")
        lines.append("-- " + "=" * 70)
        
        # Safety summary
        safe = [c for c in changes if c.safety_level == SafetyLevel.SAFE]
        warning = [c for c in changes if c.safety_level == SafetyLevel.WARNING]
        destructive = [c for c in changes if c.safety_level == SafetyLevel.DESTRUCTIVE]
        
        if warning or destructive:
            lines.append("--")
            lines.append("-- ⚠ SAFETY NOTES:")
            if destructive:
                lines.append(f"--   DESTRUCTIVE: {len(destructive)} changes may cause data loss")
            if warning:
                lines.append(f"--   WARNING: {len(warning)} changes require attention")
            if safe:
                lines.append(f"--   SAFE: {len(safe)} changes are low risk")
        else:
            lines.append("-- Safety: All changes are SAFE")
        
        lines.append("-- " + "=" * 70)
        lines.append("")
        
        # Main transaction
        lines.append("BEGIN;")
        lines.append("")
        
        # Group changes by table
        tables_with_changes: Dict[str, List[SchemaChange]] = {}
        for change in changes:
            if change.table_name not in tables_with_changes:
                tables_with_changes[change.table_name] = []
            tables_with_changes[change.table_name].append(change)
        
        # Generate SQL for each table
        for table_name, table_changes in tables_with_changes.items():
            if not table_name:  # Schema-level changes
                for change in table_changes:
                    sql = self.generate_change_sql(change)
                    if sql:
                        lines.append(sql)
                        lines.append("")
                continue
            
            # Check if table is audited
            table_def = self.get_table_definition(table_name)
            is_audited = table_def and table_def.get('generate_audit_table', False)
            
            lines.append(f"-- Changes for table: {table_name}")
            if is_audited:
                lines.append(f"-- (audited table - will update main + audit + trigger)")
            lines.append("")
            
            # Main table changes
            lines.append(f"-- Main table: {table_name}")
            for change in table_changes:
                if change.change_type != ChangeType.RECREATE_TRIGGER_FUNCTION:
                    sql = self.generate_change_sql(change)
                    if sql:
                        lines.append(sql)
                        lines.append("")
            
            # Audit table changes (if applicable)
            if is_audited:
                lines.append(f"-- Audit table: {table_name}_audr")
                audit_stmts = self.generate_audit_table_changes(table_name, table_changes)
                for stmt in audit_stmts:
                    lines.append(stmt)
                    lines.append("")
                
                # Trigger recreation
                needs_trigger_update = any(
                    c.change_type in [ChangeType.ADD_COLUMN, ChangeType.DROP_COLUMN]
                    for c in table_changes
                )
                
                if needs_trigger_update:
                    lines.append(f"-- Recreate trigger function (column changes detected)")
                    trigger_sql = self.generate_trigger_recreation(table_name)
                    if trigger_sql:
                        lines.append(trigger_sql)
                        lines.append("")
        
        lines.append("COMMIT;")
        lines.append("")
        
        # Rollback section (commented)
        lines.append("-- " + "=" * 70)
        lines.append("-- ROLLBACK (for reference)")
        lines.append("-- " + "=" * 70)
        lines.append("-- To rollback this change, you would need to:")
        lines.append("-- 1. Reverse the column additions/deletions")
        lines.append("-- 2. Restore original data types")
        lines.append("-- 3. Recreate any dropped indexes")
        lines.append("--")
        lines.append("-- Note: Some changes (like DROP COLUMN) cannot be fully reversed")
        lines.append("-- if data was not backed up beforehand.")
        
        return "\n".join(lines) + "\n"
