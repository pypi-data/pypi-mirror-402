"""
Schema loader with inheritance support.

This module loads YAML schema definitions and resolves:
- File references (extends: other_file.yaml)
- Table template inheritance (extends: standard_table)
- Field type expansion (field_type: slug)
- Column pattern expansion (column_pattern: audit)
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from copy import deepcopy
from dataclasses import dataclass


@dataclass
class LoadedSchema:
    """Represents a loaded and resolved schema."""
    schema_name: str
    description: str
    tables: List[Dict[str, Any]]
    source_file: Path
    base_definitions: Optional[Dict[str, Any]] = None


class SchemaLoader:
    """Load and resolve YAML schema definitions."""
    
    def __init__(self):
        self.loaded_files: Dict[Path, Dict] = {}
        self.base_definitions: Optional[Dict] = None
    
    def load_file(self, file_path: Path) -> Dict:
        """
        Load a YAML file and cache it.
        
        Args:
            file_path: Path to YAML file.
            
        Returns:
            Parsed YAML as dictionary.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            yaml.YAMLError: If YAML is malformed.
        """
        # Convert to absolute path
        file_path = file_path.resolve()
        
        # Check cache
        if file_path in self.loaded_files:
            return self.loaded_files[file_path]
        
        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Schema file not found: {file_path}")
        
        # Load YAML
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        
        # Cache and return
        self.loaded_files[file_path] = data
        return data
    
    def load_with_extends(self, file_path: Path) -> Dict:
        """
        Load a schema file and resolve 'extends' reference.
        
        If the schema has 'extends: other_file.yaml', loads that file
        first and makes it available as base_definitions.
        
        Args:
            file_path: Path to schema YAML file.
            
        Returns:
            Schema dictionary with extends resolved.
        """
        # Load main schema
        schema = self.load_file(file_path)
        
        # Check for extends
        if 'extends' in schema:
            extends_path = schema['extends']
            
            # Resolve relative to the schema file's directory
            base_path = file_path.parent / extends_path
            base_path = base_path.resolve()
            
            # Load base definitions
            self.base_definitions = self.load_file(base_path)
            
            # Remove extends key from schema
            schema = schema.copy()
            del schema['extends']
        
        return schema
    
    def resolve_table_inheritance(self, table: Dict) -> Dict:
        """
        Resolve table template inheritance.
        
        If table has 'extends: template_name', resolves the template
        from base_definitions and merges with table definition.
        
        Args:
            table: Table definition dictionary.
            
        Returns:
            Table with inheritance resolved.
        """
        if 'extends' not in table:
            return table
        
        if not self.base_definitions:
            raise ValueError(
                f"Table extends '{table['extends']}' but no base definitions loaded"
            )
        
        template_name = table['extends']
        
        # Get template from base definitions
        templates = self.base_definitions.get('table_templates', {})
        if template_name not in templates:
            raise ValueError(f"Table template '{template_name}' not found")
        
        template = templates[template_name]
        
        # Recursively resolve template inheritance
        if 'extends' in template:
            template = self.resolve_table_inheritance(template.copy())
        
        # Start with template
        resolved = deepcopy(template)
        
        # Merge table definition over template
        for key, value in table.items():
            if key == 'extends':
                continue
            elif key == 'columns':
                # Will be handled separately
                resolved['columns'] = value
            elif key == 'indexes' and 'standard_indexes' in resolved:
                # Merge with standard indexes
                resolved['indexes'] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def get_inherited_columns(self, table: Dict) -> List[Dict]:
        """
        Get columns that are inherited from flags/templates.
        
        Args:
            table: Table definition.
            
        Returns:
            List of column definitions.
        """
        columns = []
        
        if not self.base_definitions:
            return columns
        
        column_patterns = self.base_definitions.get('column_patterns', {})
        
        # Add audit fields if requested
        if table.get('include_audit_fields'):
            if 'audit' in column_patterns:
                columns.extend(deepcopy(column_patterns['audit']))
        
        # Add capture fields if requested
        if table.get('include_capture_fields'):
            if 'capture' in column_patterns:
                columns.extend(deepcopy(column_patterns['capture']))
        
        # Add standard columns from template and resolve field types
        if 'standard_columns' in table:
            for col in table['standard_columns']:
                col_copy = deepcopy(col)
                # If it's a field_type reference, resolve it
                if 'field_type' in col_copy:
                    # For standard columns with only field_type,
                    # use the field_type name as the column name
                    if 'name' not in col_copy:
                        col_copy['name'] = col_copy['field_type']
                    col_copy = self.resolve_field_type(col_copy)
                columns.append(col_copy)
        
        return columns
    
    def resolve_field_type(self, column: Dict) -> Dict:
        """
        Resolve field_type reference to actual column definition.
        
        Args:
            column: Column definition with field_type.
            
        Returns:
            Column with field type expanded.
        """
        if 'field_type' not in column:
            return column
        
        if not self.base_definitions:
            raise ValueError("field_type used but no base definitions loaded")
        
        field_type_name = column['field_type']
        field_types = self.base_definitions.get('field_types', {})
        
        if field_type_name not in field_types:
            raise ValueError(f"Field type '{field_type_name}' not found")
        
        # Get base field type definition
        field_def = deepcopy(field_types[field_type_name])
        
        # Preserve the name from the column
        field_def['name'] = column['name']
        
        # Allow overrides from column definition
        for key in ['constraints', 'default', 'type']:
            if key in column:
                # If both have constraints, append them
                if key == 'constraints' and key in field_def:
                    field_def[key] = f"{field_def[key]} {column[key]}"
                else:
                    field_def[key] = column[key]
        
        return field_def
    
    def expand_columns(self, table: Dict) -> List[Dict]:
        """
        Expand all columns for a table.
        
        This combines:
        - Inherited columns (audit, capture, etc.)
        - Explicit columns from table definition
        - Field type resolution
        
        Args:
            table: Table definition.
            
        Returns:
            List of fully expanded column definitions.
        """
        columns = []
        
        # Add inherited columns first
        inherited = self.get_inherited_columns(table)
        columns.extend(inherited)
        
        # Add explicit columns
        if 'columns' in table:
            for col in table['columns']:
                # Resolve field types
                expanded_col = self.resolve_field_type(col)
                columns.append(expanded_col)
        
        return columns
    
    def merge_indexes(self, table: Dict) -> List[Dict]:
        """
        Merge standard indexes with table-specific indexes.
        
        Args:
            table: Table definition.
            
        Returns:
            List of all indexes.
        """
        indexes = []
        
        # Add standard indexes from template
        if 'standard_indexes' in table:
            indexes.extend(deepcopy(table['standard_indexes']))
        
        # Add table-specific indexes
        if 'indexes' in table:
            indexes.extend(deepcopy(table['indexes']))
        
        return indexes
    
    def resolve_table(self, table: Dict) -> Dict:
        """
        Fully resolve a table definition.
        
        Args:
            table: Raw table definition from YAML.
            
        Returns:
            Fully resolved table with all inheritance expanded.
        """
        # Resolve template inheritance
        resolved = self.resolve_table_inheritance(table)
        
        # Expand columns
        resolved['_expanded_columns'] = self.expand_columns(resolved)
        
        # Merge indexes
        resolved['_all_indexes'] = self.merge_indexes(resolved)
        
        # Keep original columns for reference
        resolved['_original_columns'] = resolved.get('columns', [])
        
        return resolved
    
    def load_schema(self, file_path: Path) -> LoadedSchema:
        """
        Load a complete schema with all inheritance resolved.
        
        Args:
            file_path: Path to schema YAML file.
            
        Returns:
            LoadedSchema with all tables fully resolved.
        """
        # Convert to Path if string
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Load with extends
        schema = self.load_with_extends(file_path)
        
        # Special case: if loading base_definitions.yaml itself,
        # set base_definitions to the loaded content
        if file_path.name == 'base_definitions.yaml' and self.base_definitions is None:
            self.base_definitions = schema
        
        # Resolve all tables
        resolved_tables = []
        for table in schema.get('tables', []):
            resolved_table = self.resolve_table(table)
            resolved_tables.append(resolved_table)
        
        return LoadedSchema(
            schema_name=schema.get('schema', 'public'),
            description=schema.get('description', ''),
            tables=resolved_tables,
            source_file=file_path,
            base_definitions=self.base_definitions
        )
    
    def reset(self):
        """Reset loader state (for testing)."""
        self.loaded_files.clear()
        self.base_definitions = None

