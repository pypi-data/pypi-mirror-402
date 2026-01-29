#!/usr/bin/env python3
"""
PostgreSQL Schema Toolkit CLI

Command-line interface for YAML-based schema management.
"""

import sys
import argparse
from pathlib import Path
import psycopg2

from pg_schema_toolkit.scripts.schema_loader import SchemaLoader
from pg_schema_toolkit.scripts.ddl_generator import DDLGenerator
from pg_schema_toolkit.scripts.introspector import DatabaseIntrospector
from pg_schema_toolkit.scripts.differ import SchemaDiffer, SafetyLevel
from pg_schema_toolkit.scripts.change_generator import ChangeGenerator
from pg_schema_toolkit.scripts.db_config import get_config

# Tab completion support
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


def cmd_validate(args):
    """Validate a YAML schema file."""
    print(f"Validating schema: {args.schema_file}")
    
    try:
        loader = SchemaLoader()
        schema = loader.load_schema(Path(args.schema_file))
        
        print(f"✓ Schema is valid!")
        print(f"  Schema name: {schema.schema_name}")
        print(f"  Tables: {len(schema.tables)}")
        
        for table in schema.tables:
            print(f"    - {table['name']}: {len(table['_expanded_columns'])} columns")
        
        return 0
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_generate(args):
    """Generate DDL from YAML schema."""
    print(f"Generating DDL from: {args.schema_file}")
    
    try:
        # Load schema
        loader = SchemaLoader()
        schema = loader.load_schema(Path(args.schema_file))
        
        print(f"✓ Schema loaded: {schema.schema_name}")
        print(f"  Tables: {len(schema.tables)}")
        
        # Generate DDL
        generator = DDLGenerator(schema)
        ddl = generator.generate_all()
        
        # Output
        if args.output:
            output_path = Path(args.output)
            generator.write_to_file(output_path)
            print(f"✓ DDL written to: {output_path}")
        else:
            print("\n" + "=" * 70)
            print(ddl)
            print("=" * 70)
        
        return 0
    
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_info(args):
    """Show database connection info."""
    print("Database Connection Information\n")
    
    try:
        config = get_config()
        config.validate()
        
        print(f"\n✓ Configuration loaded successfully")
        print(f"  psycopg2 connection params available")
        
        return 0
    
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nRequired environment variables:")
        print("  - PGHOST")
        print("  - PGPORT")
        print("  - PGDATABASE")
        print("  - PGUSER")
        print("\nOptional:")
        print("  - PGPASSWORD (or use ~/.pgpass)")
        print("  - DB_SCHEMA (default: public)")
        print("  - DB_CONNECT_TIMEOUT (default: 10 seconds)")
        print("  - ENVIRONMENT (default: development)")
        return 1


def cmd_diff(args):
    """Show differences between YAML schema and database."""
    print(f"Comparing schema: {args.schema_file}")
    print()
    
    try:
        # Load YAML schema
        loader = SchemaLoader()
        schema = loader.load_schema(Path(args.schema_file))
        
        print(f"✓ Schema loaded: {schema.schema_name}")
        print(f"  Tables: {len(schema.tables)}")
        print()
        
        # Connect to database
        config = get_config()
        conn = psycopg2.connect(**config.psycopg2_params)
        
        try:
            # Introspect database
            introspector = DatabaseIntrospector(conn)
            print(f"✓ Connected to database: {config.name}")
            print()
            
            # Compare schemas
            differ = SchemaDiffer(schema, introspector)
            changes = differ.compare_schemas()
            
            if not changes:
                print(f"✓ Schema '{schema.schema_name}' is up to date with database")
                print("  No changes needed")
                return 0
            
            # Group by safety level
            grouped = differ.group_changes_by_safety(changes)
            
            print(f"Changes detected: {len(changes)}")
            print()
            
            # Show safe changes
            if grouped[SafetyLevel.SAFE]:
                print("Safe changes:")
                for change in grouped[SafetyLevel.SAFE]:
                    print(f"  {change}")
                print()
            
            # Show warning changes
            if grouped[SafetyLevel.WARNING]:
                print("⚠ Changes requiring attention:")
                for change in grouped[SafetyLevel.WARNING]:
                    print(f"  {change}")
                print()
            
            # Show destructive changes
            if grouped[SafetyLevel.DESTRUCTIVE]:
                print("✗ DESTRUCTIVE changes:")
                for change in grouped[SafetyLevel.DESTRUCTIVE]:
                    print(f"  {change}")
                print()
            
            # Show next steps
            print("To generate schema change file:")
            print(f"  pg-schema generate-change {args.schema_file} -m 'Description'")
            
            return 0
            
        finally:
            conn.close()
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        print()
        print("Make sure environment variables are set:")
        print("  PGHOST, PGPORT, PGDATABASE, PGUSER")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_generate_change(args):
    """Generate schema change file from YAML diff."""
    print(f"Generating schema change from: {args.schema_file}")
    print()
    
    try:
        # Load YAML schema
        loader = SchemaLoader()
        schema = loader.load_schema(Path(args.schema_file))
        
        print(f"✓ Schema loaded: {schema.schema_name}")
        print()
        
        # Connect to database and get changes
        config = get_config()
        conn = psycopg2.connect(**config.psycopg2_params)
        
        try:
            introspector = DatabaseIntrospector(conn)
            differ = SchemaDiffer(schema, introspector)
            changes = differ.compare_schemas()
            
            if not changes:
                print("✓ No changes detected - schema is up to date")
                return 0
            
            print(f"✓ Detected {len(changes)} changes")
            
            # Show summary
            grouped = differ.group_changes_by_safety(changes)
            print(f"  Safe: {len(grouped[SafetyLevel.SAFE])}")
            print(f"  Warning: {len(grouped[SafetyLevel.WARNING])}")
            print(f"  Destructive: {len(grouped[SafetyLevel.DESTRUCTIVE])}")
            print()
            
            # Generate change file
            generator = ChangeGenerator(schema)
            sql = generator.generate_schema_change_file(changes, args.message)
            
            # Determine output file
            if args.output:
                output_path = Path(args.output)
            else:
                # Auto-generate filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_message = args.message.replace(' ', '_').replace('/', '_')[:40]
                filename = f"change_{timestamp}_{safe_message}.sql"
                output_path = Path('schema_changes') / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(output_path, 'w') as f:
                f.write(sql)
            
            print(f"✓ Schema change file created: {output_path}")
            print()
            print("Review the file, then apply with:")
            print(f"  psql < {output_path}")
            
            return 0
            
        finally:
            conn.close()
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='PostgreSQL Schema Toolkit - YAML-based schema management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a schema
  pg-schema validate schema/users.yaml
  
  # Generate DDL
  pg-schema generate schema/users.yaml -o create_users.sql
  
  # Compare with database
  pg-schema diff schema/users.yaml
  
  # Generate change file
  pg-schema generate-change schema/users.yaml -m "Add email column"
  
  # Show database info
  pg-schema info
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output with stack traces')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # validate command
    validate_parser = subparsers.add_parser('validate',
                                           help='Validate a YAML schema file')
    validate_parser.add_argument('schema_file', help='Path to YAML schema file')
    validate_parser.set_defaults(func=cmd_validate)
    
    # generate command
    generate_parser = subparsers.add_parser('generate',
                                           help='Generate DDL from YAML schema')
    generate_parser.add_argument('schema_file', help='Path to YAML schema file')
    generate_parser.add_argument('-o', '--output', help='Output SQL file')
    generate_parser.set_defaults(func=cmd_generate)
    
    # info command
    info_parser = subparsers.add_parser('info',
                                       help='Show database connection info')
    info_parser.set_defaults(func=cmd_info)
    
    # diff command
    diff_parser = subparsers.add_parser('diff',
                                       help='Compare YAML schema with database')
    diff_parser.add_argument('schema_file', help='Path to YAML schema file')
    diff_parser.set_defaults(func=cmd_diff)
    
    # generate-change command
    change_parser = subparsers.add_parser('generate-change',
                                         help='Generate schema change file')
    change_parser.add_argument('schema_file', help='Path to YAML schema file')
    change_parser.add_argument('-m', '--message', required=True,
                              help='Change description')
    change_parser.add_argument('-o', '--output', help='Output SQL file')
    change_parser.set_defaults(func=cmd_generate_change)
    
    # Enable tab completion if available
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130


if __name__ == '__main__':
    sys.exit(main())
