"""
Database Introspector - Read current schema from PostgreSQL

This module queries PostgreSQL system catalogs to understand the current
database schema structure for comparison with YAML definitions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import psycopg2


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]
    constraints: List[str]  # PRIMARY KEY, UNIQUE, etc.
    
    def get_full_type(self) -> str:
        """
        Reconstruct full type string with precision/scale/length.
        
        Returns:
            Full type string (e.g., "NUMERIC(10,2)", "VARCHAR(255)")
        """
        base_type = self.data_type.upper()
        
        # Numeric types with precision and scale
        if base_type in ('NUMERIC', 'DECIMAL') and self.numeric_precision is not None:
            if self.numeric_scale is not None and self.numeric_scale > 0:
                return f"{base_type}({self.numeric_precision},{self.numeric_scale})"
            else:
                return f"{base_type}({self.numeric_precision})"
        
        # Character types with length
        if base_type in ('VARCHAR', 'CHAR', 'CHARACTER VARYING', 'CHARACTER') and self.character_maximum_length is not None:
            return f"{base_type}({self.character_maximum_length})"
        
        return base_type


@dataclass
class IndexInfo:
    """Information about a database index."""
    name: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    where_clause: Optional[str]


@dataclass
class TriggerInfo:
    """Information about a database trigger."""
    name: str
    function_name: str
    timing: str  # BEFORE, AFTER
    events: List[str]  # INSERT, UPDATE, DELETE
    for_each: str  # ROW, STATEMENT


@dataclass
class TableInfo:
    """Complete information about a database table."""
    schema_name: str
    table_name: str
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    triggers: List[TriggerInfo]
    unique_constraints: List[List[str]]


class DatabaseIntrospector:
    """
    Introspect PostgreSQL database to understand current schema.
    
    Reads tables, columns, indexes, constraints, and triggers from
    PostgreSQL system catalogs.
    """
    
    def __init__(self, config_or_connection):
        """
        Initialize introspector with database config or connection.
        
        Args:
            config_or_connection: DatabaseConfig object or psycopg2 connection
        """
        # Accept either DatabaseConfig or connection for flexibility
        if hasattr(config_or_connection, 'host'):  # It's a DatabaseConfig
            self.config = config_or_connection
            self.conn = psycopg2.connect(
                host=config_or_connection.host,
                port=config_or_connection.port,
                dbname=config_or_connection.name,
                user=config_or_connection.user,
                password=config_or_connection.password,
            )
            self._owns_connection = True
        else:  # It's already a connection
            self.conn = config_or_connection
            self.config = None
            self._owns_connection = False
    
    def introspect_columns(self, schema_name: str, table_name: str) -> List[ColumnInfo]:
        """
        Get all columns for a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            List of ColumnInfo objects
        """
        query = """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                -- Check for PRIMARY KEY
                CASE WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY' ELSE NULL END as is_primary,
                -- Check for UNIQUE
                CASE WHEN uq.column_name IS NOT NULL THEN 'UNIQUE' ELSE NULL END as is_unique
            FROM information_schema.columns c
            -- PRIMARY KEY check
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            ) pk ON c.column_name = pk.column_name
            -- UNIQUE check
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'UNIQUE'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            ) uq ON c.column_name = uq.column_name
            WHERE c.table_schema = %s 
                AND c.table_name = %s
            ORDER BY c.ordinal_position
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name, schema_name, table_name, 
                               schema_name, table_name))
            columns = []
            for row in cur.fetchall():
                constraints = []
                if row[7]:  # is_primary
                    constraints.append('PRIMARY KEY')
                if row[8]:  # is_unique
                    constraints.append('UNIQUE')
                if row[2] == 'NO':  # is_nullable
                    constraints.append('NOT NULL')
                
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1].upper(),
                    is_nullable=(row[2] == 'YES'),
                    column_default=row[3],
                    character_maximum_length=row[4],
                    numeric_precision=row[5],
                    numeric_scale=row[6],
                    constraints=constraints
                ))
            
            return columns
    
    def introspect_indexes(self, schema_name: str, table_name: str) -> List[IndexInfo]:
        """
        Get all indexes for a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            List of IndexInfo objects
        """
        query = """
            SELECT 
                i.relname as index_name,
                array_agg(a.attname ORDER BY k.ordinality) as column_names,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary,
                pg_get_expr(ix.indpred, ix.indrelid) as where_clause
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            CROSS JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS k(attnum, ordinality)
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
            WHERE n.nspname = %s 
                AND t.relname = %s
            GROUP BY i.relname, ix.indisunique, ix.indisprimary, ix.indpred, ix.indrelid
            ORDER BY i.relname
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            indexes = []
            for row in cur.fetchall():
                indexes.append(IndexInfo(
                    name=row[0],
                    columns=row[1],
                    is_unique=row[2],
                    is_primary=row[3],
                    where_clause=row[4]
                ))
            
            return indexes
    
    def introspect_triggers(self, schema_name: str, table_name: str) -> List[TriggerInfo]:
        """
        Get all triggers for a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            List of TriggerInfo objects
        """
        query = """
            SELECT 
                t.tgname as trigger_name,
                p.proname as function_name,
                CASE t.tgtype & 2
                    WHEN 0 THEN 'AFTER'
                    ELSE 'BEFORE'
                END as timing,
                CASE 
                    WHEN t.tgtype & 4 = 4 THEN 'INSERT'
                    ELSE NULL
                END as has_insert,
                CASE 
                    WHEN t.tgtype & 8 = 8 THEN 'DELETE'
                    ELSE NULL
                END as has_delete,
                CASE 
                    WHEN t.tgtype & 16 = 16 THEN 'UPDATE'
                    ELSE NULL
                END as has_update,
                CASE t.tgtype & 1
                    WHEN 1 THEN 'ROW'
                    ELSE 'STATEMENT'
                END as for_each
            FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_proc p ON t.tgfoid = p.oid
            WHERE n.nspname = %s 
                AND c.relname = %s
                AND NOT t.tgisinternal
            ORDER BY t.tgname
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            triggers = []
            for row in cur.fetchall():
                events = []
                if row[3]:  # has_insert
                    events.append('INSERT')
                if row[4]:  # has_delete
                    events.append('DELETE')
                if row[5]:  # has_update
                    events.append('UPDATE')
                
                triggers.append(TriggerInfo(
                    name=row[0],
                    function_name=row[1],
                    timing=row[2],
                    events=events,
                    for_each=row[6]
                ))
            
            return triggers
    
    def introspect_unique_constraints(self, schema_name: str, table_name: str) -> List[List[str]]:
        """
        Get unique constraints (table-level).
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            List of column lists (each list represents one unique constraint)
        """
        query = """
            SELECT array_agg(kcu.column_name ORDER BY kcu.ordinal_position)
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_schema = %s
                AND tc.table_name = %s
            GROUP BY tc.constraint_name
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            return [row[0] for row in cur.fetchall()]
    
    def introspect_table(self, schema_name: str, table_name: str) -> TableInfo:
        """
        Get complete information about a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            TableInfo object with complete table structure
        """
        return TableInfo(
            schema_name=schema_name,
            table_name=table_name,
            columns=self.introspect_columns(schema_name, table_name),
            indexes=self.introspect_indexes(schema_name, table_name),
            triggers=self.introspect_triggers(schema_name, table_name),
            unique_constraints=self.introspect_unique_constraints(schema_name, table_name)
        )
    
    def introspect_schema(self, schema_name: str) -> Dict[str, TableInfo]:
        """
        Get all tables in a schema.
        
        Args:
            schema_name: Schema name
            
        Returns:
            Dictionary mapping table names to TableInfo objects
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name,))
            tables = {}
            for (table_name,) in cur.fetchall():
                tables[table_name] = self.introspect_table(schema_name, table_name)
            
            return tables
    
    def table_exists(self, schema_name: str, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            True if table exists
        """
        query = """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                    AND table_name = %s
            )
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            return cur.fetchone()[0]
    
    def schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema exists.
        
        Args:
            schema_name: Schema name
            
        Returns:
            True if schema exists
        """
        query = """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            )
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name,))
            return cur.fetchone()[0]
    
    def list_schemas(self) -> List[str]:
        """
        List all schemas in the database.
        
        Returns:
            List of schema names
        """
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]
    
    def list_tables(self, schema_name: str) -> List[str]:
        """
        List all tables in a schema.
        
        Args:
            schema_name: Schema name
            
        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name,))
            return [row[0] for row in cur.fetchall()]
    
    def introspect_primary_key(self, schema_name: str, table_name: str) -> Optional[List[str]]:
        """
        Get primary key columns for a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            List of primary key column names, or None if no PK
        """
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = (%s || '.' || %s)::regclass
              AND i.indisprimary
            ORDER BY a.attnum
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (schema_name, table_name))
                pk_cols = [row[0] for row in cur.fetchall()]
                return pk_cols if pk_cols else None
        except:
            return None

