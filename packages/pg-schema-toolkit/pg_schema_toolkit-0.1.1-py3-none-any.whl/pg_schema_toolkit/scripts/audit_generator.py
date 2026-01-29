"""
Audit Table Generator

Generates audit tables, trigger functions, and triggers for tables marked
with generate_audit_table=true.

Audit tables capture complete history of INSERT, UPDATE, DELETE operations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


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


@dataclass
class AuditConfig:
    """Configuration for audit table generation."""
    audit_table_suffix: str
    audit_function_prefix: str
    audit_trigger_suffix: str
    preserve_dropped_columns: bool
    audit_table_indexes: bool
    audit_metadata_columns: List[Dict[str, Any]]
    standard_audit_indexes: List[Dict[str, Any]]


class AuditTableGenerator:
    """
    Generates DDL for audit tables and triggers.
    
    For a table marked with generate_audit_table=true, generates:
    1. Audit table with metadata + snapshot columns
    2. Trigger function to capture changes
    3. Trigger to invoke function on INSERT/UPDATE/DELETE
    4. Indexes on audit table
    """
    
    def __init__(self, audit_config: Dict[str, Any]):
        """
        Initialize with audit configuration from base_definitions.yaml.
        
        Args:
            audit_config: audit_config section from base_definitions
        """
        self.config = AuditConfig(
            audit_table_suffix=audit_config.get('audit_table_suffix', '_audr'),
            audit_function_prefix=audit_config.get('audit_function_prefix', 'audit_'),
            audit_trigger_suffix=audit_config.get('audit_trigger_suffix', '_trigger'),
            preserve_dropped_columns=audit_config.get('preserve_dropped_columns', True),
            audit_table_indexes=audit_config.get('audit_table_indexes', True),
            audit_metadata_columns=audit_config.get('audit_metadata_columns', []),
            standard_audit_indexes=audit_config.get('standard_audit_indexes', [])
        )
    
    def get_audit_table_name(self, table_name: str) -> str:
        """Get audit table name for a given table."""
        return f"{table_name}{self.config.audit_table_suffix}"
    
    def get_trigger_function_name(self, table_name: str) -> str:
        """Get trigger function name for a given table."""
        return f"{self.config.audit_function_prefix}{table_name}"
    
    def get_trigger_name(self, table_name: str) -> str:
        """Get trigger name for a given table."""
        return f"{self.config.audit_function_prefix}{table_name}{self.config.audit_trigger_suffix}"
    
    def generate_audit_table_ddl(self, schema_name: str, table_name: str, 
                                  main_table_columns: List[Dict[str, Any]]) -> str:
        """
        Generate CREATE TABLE statement for audit table.
        
        Args:
            schema_name: Schema name
            table_name: Main table name
            main_table_columns: List of columns from main table (already expanded)
        
        Returns:
            CREATE TABLE DDL for audit table
        """
        audit_table_name = self.get_audit_table_name(table_name)
        
        lines = []
        lines.append(f"-- Audit table for {table_name}")
        lines.append(f"CREATE TABLE {schema_name}.{audit_table_name} (")
        
        # Add audit metadata columns
        column_defs = []
        for meta_col in self.config.audit_metadata_columns:
            col_def = f"    {meta_col['name']} {meta_col['type']}"
            if meta_col.get('constraints'):
                col_def += f" {meta_col['constraints']}"
            if meta_col.get('default'):
                col_def += f" DEFAULT {meta_col['default']}"
            column_defs.append(col_def)
        
        # Add snapshot columns from main table (without constraints)
        for col in main_table_columns:
            # Skip the primary key column - we already have audit_row_id
            constraints = col.get('constraints', '')
            if 'PRIMARY KEY' in constraints:
                continue
            
            col_def = f"    {col['name']} {col['type']}"
            # Don't add constraints (NOT NULL, UNIQUE, etc.) in audit table
            # Audit table stores snapshots, so nullability doesn't matter
            column_defs.append(col_def)
        
        lines.append(",\n".join(column_defs))
        lines.append(");")
        lines.append("")
        
        # Add comments
        lines.append(f"COMMENT ON TABLE {schema_name}.{audit_table_name} IS ")
        lines.append(f"    'Audit trail for {schema_name}.{table_name} - captures all INSERT/UPDATE/DELETE operations';")
        lines.append("")
        
        for meta_col in self.config.audit_metadata_columns:
            if meta_col.get('description'):
                lines.append(f"COMMENT ON COLUMN {schema_name}.{audit_table_name}.{meta_col['name']} IS ")
                lines.append(f"    '{meta_col['description']}';")

        return clean_sql("\n".join(lines))
    
    def generate_audit_indexes(self, schema_name: str, table_name: str) -> str:
        """
        Generate index DDL for audit table.
        
        Args:
            schema_name: Schema name
            table_name: Main table name
        
        Returns:
            CREATE INDEX statements for audit table
        """
        if not self.config.audit_table_indexes:
            return ""
        
        audit_table_name = self.get_audit_table_name(table_name)
        lines = []
        
        for idx_def in self.config.standard_audit_indexes:
            columns = idx_def['columns']
            col_list = ", ".join(columns)
            idx_name = f"idx_{audit_table_name}_{'_'.join(columns)}"
            
            lines.append(f"CREATE INDEX {idx_name} ")
            lines.append(f"    ON {schema_name}.{audit_table_name}({col_list});")
            
            if idx_def.get('description'):
                lines.append(f"COMMENT ON INDEX {schema_name}.{idx_name} IS ")
                lines.append(f"    '{idx_def['description']}';")
            lines.append("")

        return clean_sql("\n".join(lines))
    
    def generate_trigger_function(self, schema_name: str, table_name: str,
                                   main_table_columns: List[Dict[str, Any]]) -> str:
        """
        Generate trigger function for audit trail.
        
        Args:
            schema_name: Schema name
            table_name: Main table name
            main_table_columns: List of columns from main table
        
        Returns:
            CREATE FUNCTION DDL for trigger function
        """
        function_name = self.get_trigger_function_name(table_name)
        audit_table_name = self.get_audit_table_name(table_name)
        
        # Build column lists (skip primary key - we have audit_row_id)
        data_columns = [c for c in main_table_columns if 'PRIMARY KEY' not in c.get('constraints', '')]
        all_columns = ['audit_operation', 'audit_row_id'] + [c['name'] for c in data_columns]
        col_list = ", ".join(all_columns)
        
        lines = []
        lines.append(f"-- Trigger function for {table_name} audit trail")
        lines.append(f"CREATE OR REPLACE FUNCTION {schema_name}.{function_name}()")
        lines.append("RETURNS TRIGGER AS $$")
        lines.append("BEGIN")
        
        # DELETE operation
        lines.append("    IF (TG_OP = 'DELETE') THEN")
        lines.append(f"        INSERT INTO {schema_name}.{audit_table_name} (")
        lines.append(f"            {col_list}")
        lines.append("        ) VALUES (")
        old_values = ["'DELETE'", "OLD.id"] + [f"OLD.{c['name']}" for c in data_columns]
        lines.append(f"            {', '.join(old_values)}")
        lines.append("        );")
        lines.append("        RETURN OLD;")
        
        # UPDATE operation
        lines.append("    ELSIF (TG_OP = 'UPDATE') THEN")
        lines.append(f"        INSERT INTO {schema_name}.{audit_table_name} (")
        lines.append(f"            {col_list}")
        lines.append("        ) VALUES (")
        new_values = ["'UPDATE'", "NEW.id"] + [f"NEW.{c['name']}" for c in data_columns]
        lines.append(f"            {', '.join(new_values)}")
        lines.append("        );")
        lines.append("        RETURN NEW;")
        
        # INSERT operation
        lines.append("    ELSIF (TG_OP = 'INSERT') THEN")
        lines.append(f"        INSERT INTO {schema_name}.{audit_table_name} (")
        lines.append(f"            {col_list}")
        lines.append("        ) VALUES (")
        insert_values = ["'INSERT'", "NEW.id"] + [f"NEW.{c['name']}" for c in data_columns]
        lines.append(f"            {', '.join(insert_values)}")
        lines.append("        );")
        lines.append("        RETURN NEW;")
        
        lines.append("    END IF;")
        lines.append("END;")
        lines.append("$$ LANGUAGE plpgsql;")
        lines.append("")
        
        lines.append(f"COMMENT ON FUNCTION {schema_name}.{function_name}() IS ")
        lines.append(f"    'Audit trigger function for {schema_name}.{table_name}';")

        return clean_sql("\n".join(lines))
    
    def generate_trigger(self, schema_name: str, table_name: str) -> str:
        """
        Generate trigger DDL.
        
        Args:
            schema_name: Schema name
            table_name: Main table name
        
        Returns:
            CREATE TRIGGER DDL
        """
        trigger_name = self.get_trigger_name(table_name)
        function_name = self.get_trigger_function_name(table_name)
        
        lines = []
        lines.append(f"-- Trigger for {table_name} audit trail")
        lines.append(f"CREATE TRIGGER {trigger_name}")
        lines.append(f"    AFTER INSERT OR UPDATE OR DELETE ON {schema_name}.{table_name}")
        lines.append(f"    FOR EACH ROW EXECUTE FUNCTION {schema_name}.{function_name}();")
        lines.append("")
        
        lines.append(f"COMMENT ON TRIGGER {trigger_name} ON {schema_name}.{table_name} IS ")
        lines.append(f"    'Captures all changes to {schema_name}.{table_name} in audit table';")

        return clean_sql("\n".join(lines))
    
    def generate_all_audit_ddl(self, schema_name: str, table_name: str,
                                main_table_columns: List[Dict[str, Any]]) -> str:
        """
        Generate complete audit infrastructure for a table.
        
        Args:
            schema_name: Schema name
            table_name: Main table name
            main_table_columns: List of columns from main table
        
        Returns:
            Complete DDL for audit table, indexes, function, and trigger
        """
        sections = []
        
        sections.append("-- " + "=" * 70)
        sections.append(f"-- AUDIT INFRASTRUCTURE FOR {table_name}")
        sections.append("-- " + "=" * 70)
        sections.append("")
        
        sections.append(self.generate_audit_table_ddl(schema_name, table_name, main_table_columns))
        sections.append("")
        
        sections.append(self.generate_audit_indexes(schema_name, table_name))
        sections.append("")
        
        sections.append(self.generate_trigger_function(schema_name, table_name, main_table_columns))
        sections.append("")
        
        sections.append(self.generate_trigger(schema_name, table_name))
        sections.append("")

        return clean_sql("\n".join(sections))
