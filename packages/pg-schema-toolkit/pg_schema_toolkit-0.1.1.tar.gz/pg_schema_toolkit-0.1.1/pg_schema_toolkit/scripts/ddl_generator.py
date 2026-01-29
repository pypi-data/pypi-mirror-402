"""
DDL Generator - Convert resolved YAML schemas to PostgreSQL DDL.

This module takes a LoadedSchema and generates clean, well-formatted
PostgreSQL CREATE TABLE statements with optional audit table support.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from pg_schema_toolkit.scripts.schema_loader import LoadedSchema
from pg_schema_toolkit.scripts.audit_generator import AuditTableGenerator


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


class DDLGenerator:
    """Generate PostgreSQL DDL from resolved schemas with audit table support."""
    
    def __init__(self, schema: LoadedSchema):
        """
        Initialize generator with a loaded schema.
        
        Args:
            schema: LoadedSchema from schema_loader.
        """
        self.schema = schema
        
        # Initialize audit generator if audit_config exists
        self.audit_generator: Optional[AuditTableGenerator] = None
        if hasattr(schema, 'base_definitions') and schema.base_definitions:
            audit_config = schema.base_definitions.get('audit_config')
            if audit_config:
                self.audit_generator = AuditTableGenerator(audit_config)
    
    def generate_column_ddl(self, column: Dict[str, Any]) -> str:
        """
        Generate DDL for a single column.
        
        Args:
            column: Column definition dict.
            
        Returns:
            Column DDL string (e.g., "id BIGSERIAL PRIMARY KEY").
        """
        parts = []
        
        # Column name
        parts.append(f"    {column['name']}")
        
        # Data type
        col_type = column['type']
        parts.append(col_type)
        
        # Default value
        if 'default' in column:
            default_val = column['default']
            # For JSONB columns, ensure type casting is applied
            if col_type.upper() == 'JSONB' and '::jsonb' not in default_val.lower():
                # Ensure JSON values are quoted (unless already a string literal or function)
                if not (default_val.startswith("'") or default_val.upper().startswith(('NULL', 'CURRENT_'))):
                    default_val = f"'{default_val}'"
                default_val = f"{default_val}::jsonb"
            parts.append(f"DEFAULT {default_val}")
        
        # Constraints
        if 'constraints' in column:
            parts.append(column['constraints'])
        
        return " ".join(parts)
    
    def generate_table_ddl(self, table: Dict[str, Any]) -> str:
        """
        Generate DDL for a complete table.
        
        Args:
            table: Resolved table definition.
            
        Returns:
            Complete CREATE TABLE statement.
        """
        lines = []
        
        # Header comment (handle multi-line descriptions)
        if 'description' in table:
            desc_lines = table['description'].strip().split('\n')
            for desc_line in desc_lines:
                lines.append(f"-- {desc_line}")
        
        # CREATE TABLE
        table_name = f"{self.schema.schema_name}.{table['name']}"
        lines.append(f"CREATE TABLE {table_name} (")
        
        # Columns
        column_ddls = []
        for column in table['_expanded_columns']:
            column_ddls.append(self.generate_column_ddl(column))
        
        # Unique constraints (table-level)
        unique_constraints = table.get('unique_constraints', [])
        for uc in unique_constraints:
            cols = ", ".join(uc['columns'])
            column_ddls.append(f"    UNIQUE({cols})")
        
        # Join columns
        lines.append(",\n".join(column_ddls))
        
        lines.append(");")
        
        # Indexes
        index_lines = self.generate_indexes_ddl(table)
        if index_lines:
            lines.append("")
            lines.extend(index_lines)

        return clean_sql("\n".join(lines))
    
    def generate_indexes_ddl(self, table: Dict[str, Any]) -> List[str]:
        """
        Generate DDL for all indexes on a table.
        
        Args:
            table: Table definition.
            
        Returns:
            List of CREATE INDEX statements.
        """
        lines = []
        table_name = f"{self.schema.schema_name}.{table['name']}"
        
        for i, index in enumerate(table.get('_all_indexes', [])):
            # Generate index name
            if 'name' in index:
                index_name = index['name']
            else:
                col_names = "_".join(index['columns'])
                index_name = f"idx_{table['name']}_{col_names}"
            
            # Column list
            cols = ", ".join(index['columns'])
            
            # WHERE clause (for partial indexes)
            where_clause = ""
            if 'where' in index:
                where_clause = f" WHERE {index['where']}"
            
            # CREATE INDEX statement
            lines.append(
                f"CREATE INDEX {index_name} ON {table_name}({cols}){where_clause};"
            )
        
        return lines
    
    def should_generate_audit_table(self, table: Dict[str, Any]) -> bool:
        """
        Check if audit table should be generated for this table.
        
        Args:
            table: Table definition
            
        Returns:
            True if audit infrastructure should be generated
        """
        return (self.audit_generator is not None and 
                table.get('generate_audit_table', False))
    
    def generate_all(self) -> str:
        """
        Generate complete DDL for all tables in schema, including audit tables.
        
        Returns:
            Complete SQL DDL script.
        """
        lines = []
        
        # Header
        lines.append("-- " + "=" * 70)
        lines.append(f"-- Schema: {self.schema.schema_name}")
        if self.schema.description:
            # Handle multi-line schema descriptions
            desc_lines = self.schema.description.strip().split('\n')
            if len(desc_lines) == 1:
                lines.append(f"-- Description: {desc_lines[0]}")
            else:
                lines.append("-- Description:")
                for desc_line in desc_lines:
                    lines.append(f"--   {desc_line}")
        lines.append(f"-- Generated from: {self.schema.source_file.name}")
        lines.append("-- " + "=" * 70)
        lines.append("-- DO NOT EDIT THIS FILE DIRECTLY")
        lines.append("-- Source of truth: YAML schema files")
        lines.append("-- " + "=" * 70)
        lines.append("")
        
        # Create schema if not public
        if self.schema.schema_name != 'public':
            lines.append(f"CREATE SCHEMA IF NOT EXISTS {self.schema.schema_name};")
            lines.append("")
        
        # Generate each table
        for i, table in enumerate(self.schema.tables):
            if i > 0:
                lines.append("")
                lines.append("")
            
            # Main table
            table_ddl = self.generate_table_ddl(table)
            lines.append(table_ddl)
            
            # Audit table infrastructure (if requested)
            if self.should_generate_audit_table(table):
                lines.append("")
                lines.append("")
                audit_ddl = self.audit_generator.generate_all_audit_ddl(
                    self.schema.schema_name,
                    table['name'],
                    table['_expanded_columns']
                )
                lines.append(audit_ddl)

        return clean_sql("\n".join(lines)) + "\n"
    
    def write_to_file(self, output_path: Path) -> None:
        """
        Generate DDL and write to file.
        
        Args:
            output_path: Where to write the SQL file.
        """
        ddl = self.generate_all()
        
        with open(output_path, 'w') as f:
            f.write(ddl)


def generate_ddl(schema: LoadedSchema, output_path: Path = None) -> str:
    """
    Convenience function to generate DDL from a schema.
    
    Args:
        schema: LoadedSchema instance.
        output_path: Optional path to write SQL file.
        
    Returns:
        Generated DDL as string.
    """
    generator = DDLGenerator(schema)
    ddl = generator.generate_all()
    
    if output_path:
        generator.write_to_file(output_path)
    
    return ddl
