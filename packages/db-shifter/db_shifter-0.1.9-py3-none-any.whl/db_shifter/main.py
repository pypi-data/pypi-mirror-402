import psycopg2
from psycopg2.extras import RealDictCursor, Json
from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PkgNotFound
import sys
import argparse
from collections import defaultdict
import os
import json
import csv
from typing import List, Dict, Any, Optional

# ANSI color codes for beautiful CLI output
class Colors:
    """ANSI color codes for terminal output."""
    # Reset
    RESET = '\033[0m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

def colorize(text, color):
    """Apply color to text if output is a TTY, otherwise return plain text."""
    if os.isatty(sys.stdout.fileno()):
        return f"{color}{text}{Colors.RESET}"
    return text

# ===================== CLI OPTIONS ===================== #
def _resolve_version():
    try:
        return _pkg_version("db-shifter")
    except _PkgNotFound:
        return "unknown"

# Check if this looks like an insert command (has --db-url and --table but no --old-db-url)
is_insert_mode = '--db-url' in sys.argv and '--table' in sys.argv and '--old-db-url' not in sys.argv

if is_insert_mode:
    # Insert mode
    parser = argparse.ArgumentParser(description="Insert records into a PostgreSQL database table.")
    parser.add_argument("--db-url", required=True, help="Database connection string")
    parser.add_argument("--table", required=True, help="Table name to insert into")
    parser.add_argument("--data", help="JSON data (single object or array of objects)")
    parser.add_argument("--file", help="Path to JSON or CSV file containing records")
    parser.add_argument("--dry-run", action="store_true", help="Don't insert, just show what would happen")
    parser.add_argument("--verbose", action="store_true", help="Print all operations in detail")
    parser.add_argument("--skip-fk", action="store_true", help="Ignore foreign key errors")
    parser.add_argument("--on-conflict", choices=['ignore', 'update', 'error'], default='error', 
                      help="What to do on primary key conflict: ignore, update, or error (default)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_resolve_version()}")
    args = parser.parse_args()
    args.command = 'insert'
else:
    # Sync mode (default/backward compatible)
    parser = argparse.ArgumentParser(description="Move missing rows from old Postgres DB to new one.")
    parser.add_argument("--old-db-url", required=True, help="Old DB connection string")
    parser.add_argument("--new-db-url", required=True, help="New DB connection string")
    parser.add_argument("--dry-run", action="store_true", help="Don't insert, just show what would happen")
    parser.add_argument("--verbose", action="store_true", help="Print all operations in detail")
    parser.add_argument("--table", help="Sync just one table")
    parser.add_argument("--skip-fk", action="store_true", help="Ignore foreign key errors")
    parser.add_argument("--columns", help="Comma-separated list of columns to sync (e.g., 'id,name,email'). If not specified, all common columns are synced.")
    parser.add_argument("--deep-check", action="store_true", help="Deep check: compare column values for existing rows and update differences")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_resolve_version()}")
    args = parser.parse_args()
    args.command = 'sync'

# === A log of all table activities to generate final summary === #
sync_log = defaultdict(lambda: {"existing_new": 0, "existing_old": 0, "inserted": 0, "updated": 0, "inserted_pks": [], "updated_pks": []})


def quote_table(name: str) -> str:
    """Safely quote a table name with double quotes."""
    return f'"{name}"'


def quote_ident(name: str) -> str:
    """Safely quote a column name or identifier."""
    return f'"{name}"'


def get_all_tablez(conn):
    """Fetch all tables in the public schema."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname='public'
        """)
        return [row[0] for row in cur.fetchall()]


def sniff_primary_key(conn, table_name):
    """Identify the primary key column of a table."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                                 AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{quote_table(table_name)}'::regclass
              AND i.indisprimary;
        """)
        res = cur.fetchone()
        return res[0] if res else None


def count_rows(conn, table_name):
    """Count number of rows in a table."""
    with conn.cursor() as cur:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {quote_table(table_name)}")
            return cur.fetchone()[0]
        except Exception:
            return 0


def pull_existing_ids(conn, table_name, pk):
    """Pull primary key values already in the new DB."""
    with conn.cursor() as cur:
        try:
            cur.execute(f"SELECT {quote_ident(pk)} FROM {quote_table(table_name)}")
            return set(row[0] for row in cur.fetchall())
        except Exception:
            return set()


def pull_existing_rows(conn, table_name, pk, existing_ids, columns):
    """Pull existing rows from DB by primary key values."""
    if not existing_ids:
        return {}
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            column_list = ','.join([quote_ident(col) for col in columns])
            ids_tuple = tuple(existing_ids)
            cur.execute(
                f"SELECT {column_list} FROM {quote_table(table_name)} WHERE {quote_ident(pk)} IN %s",
                (ids_tuple,)
            )
            return {row[pk]: row for row in cur.fetchall()}
        except Exception:
            return {}


def get_table_columns(conn, table_name):
    """Get column names, types, and constraints for a table."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT 
                column_name, 
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        return {
            row[0]: {
                'type': row[1], 
                'nullable': row[2] == 'YES',
                'default': row[3]
            } 
            for row in cur.fetchall()
        }


def get_foreign_keys(conn, table_name):
    """Get all foreign key relationships for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
                AND tc.table_schema = 'public'
        """, (table_name,))
        return [
            {
                'constraint_name': row[0],
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            }
            for row in cur.fetchall()
        ]


def detect_circular_fks(conn, tables):
    """Detect circular foreign key dependencies between tables."""
    fk_map = {}
    for table in tables:
        fks = get_foreign_keys(conn, table)
        fk_map[table] = [fk['referenced_table'] for fk in fks if fk['referenced_table'] in tables]
    
    # Detect cycles using DFS
    cycles = []
    visited = set()
    
    def find_cycle_path(table, path):
        """Find the actual cycle path in foreign key dependencies."""
        if table in path:
            cycle_start = path.index(table)
            return path[cycle_start:] + [table]
        
        if table in visited:
            return None
        
        visited.add(table)
        path.append(table)
        
        for ref_table in fk_map.get(table, []):
            cycle = find_cycle_path(ref_table, path)
            if cycle:
                return cycle
        
        path.pop()
        return None
    
    for table in tables:
        if table not in visited:
            cycle_path = find_cycle_path(table, [])
            if cycle_path:
                # Deduplicate cycles (same cycle might be found multiple times)
                cycle_set = set(cycle_path[:-1])  # Exclude the duplicate last element
                is_duplicate = False
                for existing_cycle in cycles:
                    existing_set = set(existing_cycle[:-1])
                    if cycle_set == existing_set:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    cycles.append(cycle_path)
    
    return cycles


def get_sync_order(conn, tables):
    """Get optimal sync order based on foreign key dependencies, handling circular FKs."""
    fk_map = {}
    for table in tables:
        fks = get_foreign_keys(conn, table)
        fk_map[table] = [fk['referenced_table'] for fk in fks if fk['referenced_table'] in tables]
    
    # Detect circular dependencies
    cycles = detect_circular_fks(conn, tables)
    
    if cycles:
        print(f"\n{colorize('WARNING:', Colors.YELLOW)} {colorize('Circular foreign key dependencies detected:', Colors.BOLD)}")
        for i, cycle in enumerate(cycles, 1):
            cycle_str = " -> ".join(cycle)
            print(f"   {colorize(f'Cycle {i}:', Colors.CYAN)} {cycle_str}")
        print(f"   {colorize('Will sync these tables in multiple passes with FK constraint handling', Colors.DIM)}")
    
    # Topological sort for non-circular dependencies
    in_degree = {table: 0 for table in tables}
    for table in tables:
        for ref_table in fk_map.get(table, []):
            if ref_table in in_degree:
                in_degree[ref_table] += 1
    
    # Separate tables into circular and non-circular groups
    circular_tables = set()
    for cycle in cycles:
        circular_tables.update(cycle)
    
    non_circular = [t for t in tables if t not in circular_tables]
    circular = [t for t in tables if t in circular_tables]
    
    # Topological sort for non-circular tables
    queue = [t for t in non_circular if in_degree[t] == 0]
    ordered = []
    
    while queue:
        table = queue.pop(0)
        ordered.append(table)
        
        for ref_table in fk_map.get(table, []):
            if ref_table in non_circular:
                in_degree[ref_table] -= 1
                if in_degree[ref_table] == 0:
                    queue.append(ref_table)
    
    # Add remaining non-circular tables (if any)
    for table in non_circular:
        if table not in ordered:
            ordered.append(table)
    
    # Add circular tables at the end (will be handled specially)
    ordered.extend(circular)
    
    return ordered, circular_tables


def get_common_columns(source_conn, dest_conn, table_name):
    """Get columns that exist in both source and destination tables."""
    source_cols = get_table_columns(source_conn, table_name)
    dest_cols = get_table_columns(dest_conn, table_name)
    
    common_cols = set(source_cols.keys()) & set(dest_cols.keys())
    missing_in_dest = set(source_cols.keys()) - set(dest_cols.keys())
    missing_in_source = set(dest_cols.keys()) - set(source_cols.keys())
    
    if missing_in_dest:
        print(f"  {colorize('Columns in source but not destination:', Colors.YELLOW)} {sorted(missing_in_dest)}")
    if missing_in_source:
        print(f"  {colorize('Columns in destination but not source:', Colors.YELLOW)} {sorted(missing_in_source)}")
    
    # Check for NOT NULL constraints that might cause issues
    not_null_issues = []
    for col in common_cols:
        if not dest_cols[col]['nullable'] and col not in source_cols:
            not_null_issues.append(col)
    
    if not_null_issues:
        print(f"  {colorize('WARNING:', Colors.YELLOW)} NOT NULL columns missing from source: {not_null_issues}")
    
    return sorted(common_cols), missing_in_dest, missing_in_source, dest_cols


def pull_missing_rows(conn, table_name, pk, existing_ids, columns=None):
    """Get rows from old DB that are NOT present in new DB."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if columns:
            # Only select common columns
            column_list = ','.join([quote_ident(col) for col in columns])
            if not existing_ids:
                cur.execute(f"SELECT {column_list} FROM {quote_table(table_name)}")
            else:
                ids_tuple = tuple(existing_ids)
                cur.execute(
                    f"SELECT {column_list} FROM {quote_table(table_name)} WHERE {quote_ident(pk)} NOT IN %s", 
                    (ids_tuple,)
                )
        else:
            # Original behavior - select all columns
            if not existing_ids:
                cur.execute(f"SELECT * FROM {quote_table(table_name)}")
            else:
                ids_tuple = tuple(existing_ids)
                cur.execute(
                    f"SELECT * FROM {quote_table(table_name)} WHERE {quote_ident(pk)} NOT IN %s", 
                    (ids_tuple,)
                )
        return cur.fetchall()


def push_rows_to_new(conn, table_name, rows, pk, dry_run=False, verbose=False, is_circular_fk=False):
    """Insert missing rows into the new DB, optionally as dry-run.
    
    Args:
        conn: Database connection
        table_name: Name of the table
        rows: List of row dictionaries to insert
        pk: Primary key column name
        dry_run: If True, don't actually insert
        verbose: If True, print detailed logs
        is_circular_fk: If True, temporarily disable FK constraints for this table
    """
    if not rows:
        return
    keys = rows[0].keys()

    dropped_constraints = []
    with conn.cursor() as cur:
        # For circular FK tables, temporarily disable FK constraints
        if is_circular_fk and not dry_run:
            try:
                # Get all FK constraints for this table
                fks = get_foreign_keys(conn, table_name)
                for fk in fks:
                    constraint_name = fk['constraint_name']
                    try:
                        cur.execute(f"ALTER TABLE {quote_table(table_name)} DROP CONSTRAINT IF EXISTS {quote_ident(constraint_name)}")
                        dropped_constraints.append({
                            'name': constraint_name,
                            'column': fk['column'],
                            'referenced_table': fk['referenced_table'],
                            'referenced_column': fk['referenced_column']
                        })
                    except Exception as drop_error:
                        print(f"  {colorize('WARNING:', Colors.YELLOW)} Could not drop constraint {constraint_name}: {drop_error}")
                if dropped_constraints:
                    conn.commit()
                    print(f"  {colorize('Temporarily disabled', Colors.CYAN)} {len(dropped_constraints)} FK constraint(s) for {table_name}")
            except Exception as e:
                print(f"  {colorize('WARNING:', Colors.YELLOW)} Could not disable FK constraints: {e}")
        
        for row in rows:
            if verbose:
                print(f"  {colorize('Inserting row:', Colors.GREEN)} {row}")
            if dry_run:
                continue
            # Adapt Python dict/list values (e.g., JSON/JSONB columns) for psycopg2
            def _adapt_value(value):
                if isinstance(value, (dict, list)):
                    return Json(value)
                return value

            vals = [_adapt_value(row[k]) for k in keys]
            placeholders = ','.join(['%s'] * len(vals))
            columns = ','.join([quote_ident(k) for k in keys])
            try:
                cur.execute(
                    f"INSERT INTO {quote_table(table_name)} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    vals
                )
                sync_log[table_name]["inserted_pks"].append(row.get(pk))
                sync_log[table_name]["inserted"] += 1
            except Exception as e:
                if args.skip_fk:
                    print(f"  {colorize('WARNING:', Colors.YELLOW)} FK error skipped: {e}")
                else:
                    raise e

        # Re-enable FK constraints for circular FK tables
        if is_circular_fk and not dry_run and dropped_constraints:
            print(f"  {colorize('Note:', Colors.CYAN)} {len(dropped_constraints)} FK constraint(s) for {table_name} were disabled.")
            if verbose:
                for fk in dropped_constraints:
                    print(f"     {colorize('-', Colors.DIM)} {fk['name']}: {table_name}.{fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")
            print(f"     {colorize('Re-add them manually after sync completes using:', Colors.YELLOW)}")
            for fk in dropped_constraints:
                print(f"     {colorize('ALTER TABLE', Colors.DIM)} {quote_table(table_name)} {colorize('ADD CONSTRAINT', Colors.DIM)} {quote_ident(fk['name'])} "
                      f"{colorize('FOREIGN KEY', Colors.DIM)} ({quote_ident(fk['column'])}) "
                      f"{colorize('REFERENCES', Colors.DIM)} {quote_table(fk['referenced_table'])}({quote_ident(fk['referenced_column'])});")

    if not dry_run:
        conn.commit()


def update_rows_in_new(conn, table_name, rows_to_update, pk, dest_rows=None, dry_run=False, verbose=False, is_circular_fk=False):
    """Update existing rows in the new DB where column values differ.
    
    Args:
        conn: Database connection
        table_name: Name of the table
        rows_to_update: List of row dictionaries to update (with new values from source)
        pk: Primary key column name
        dest_rows: Dictionary of destination rows (pk -> row dict) for before/after comparison
        dry_run: If True, don't actually update
        verbose: If True, print detailed logs
        is_circular_fk: If True, table has circular FK dependencies
    """
    if not rows_to_update:
        return
    
    with conn.cursor() as cur:
        for row in rows_to_update:
            pk_value = row[pk]
            if verbose:
                # Show before/after comparison
                if dest_rows and pk_value in dest_rows:
                    dest_row = dest_rows[pk_value]
                    changes = []
                    for col, new_val in row.items():
                        if col == pk:
                            continue
                        old_val = dest_row.get(col)
                        if old_val != new_val:
                            # Format the change nicely
                            def format_value(val):
                                if val is None:
                                    return colorize('NULL', Colors.DIM)
                                # Format datetime objects nicely
                                if hasattr(val, 'strftime'):
                                    return val.strftime('%Y-%m-%d %H:%M:%S')
                                # Format booleans
                                if isinstance(val, bool):
                                    return str(val)
                                return str(val)
                            
                            old_str = format_value(old_val)
                            new_str = format_value(new_val)
                            changes.append(f"{colorize(col, Colors.CYAN)}: {colorize(old_str, Colors.RED)} {colorize('->', Colors.YELLOW)} {colorize(new_str, Colors.GREEN)}")
                    
                    if changes:
                        print(f"  {colorize('Updating row', Colors.MAGENTA)} {colorize(f'PK={pk_value}', Colors.BOLD + Colors.CYAN)}:")
                        for change in changes:
                            print(f"    {change}")
                else:
                    # Fallback if dest_rows not provided
                    diff_cols = {k: v for k, v in row.items() if k != pk}
                    print(f"  {colorize('Updating row:', Colors.CYAN)} {colorize(f'PK={pk_value}', Colors.BOLD)} {diff_cols}")
            if dry_run:
                continue
            
            # Adapt Python dict/list values (e.g., JSON/JSONB columns) for psycopg2
            def _adapt_value(value):
                if isinstance(value, (dict, list)):
                    return Json(value)
                return value
            
            # Get columns to update for THIS row (each row may have different columns)
            row_update_cols = [k for k in row.keys() if k != pk]
            
            if not row_update_cols:
                continue
            
            # Build SET clause for this specific row
            set_clauses = []
            set_values = []
            for col in row_update_cols:
                set_clauses.append(f"{quote_ident(col)} = %s")
                set_values.append(_adapt_value(row[col]))
            
            # Add PK value for WHERE clause
            set_values.append(row[pk])
            
            set_clause = ', '.join(set_clauses)
            
            try:
                cur.execute(
                    f"UPDATE {quote_table(table_name)} SET {set_clause} WHERE {quote_ident(pk)} = %s",
                    set_values
                )
                if cur.rowcount > 0:
                    sync_log[table_name]["updated_pks"].append(row.get(pk))
                    sync_log[table_name]["updated"] += 1
            except Exception as e:
                if args.skip_fk:
                    print(f"  {colorize('WARNING:', Colors.YELLOW)} Update error skipped: {e}")
                else:
                    raise e
    
    if not dry_run:
        conn.commit()


def compare_and_find_differences(source_rows, dest_rows, pk, columns):
    """Compare rows between source and destination and find differences.
    
    Returns:
        List of rows that need to be updated (with values from source)
    """
    rows_to_update = []
    
    for pk_value, source_row in source_rows.items():
        if pk_value not in dest_rows:
            continue  # Row doesn't exist in dest, will be handled by insert logic
        
        dest_row = dest_rows[pk_value]
        needs_update = False
        updated_row = {pk: pk_value}
        
        for col in columns:
            if col == pk:
                continue  # Skip PK comparison
            
            source_val = source_row.get(col)
            dest_val = dest_row.get(col)
            
            # Compare values (handle None cases and type differences)
            # Both None means they're equal
            if source_val is None and dest_val is None:
                continue
            
            # One is None, other is not - they differ
            if source_val is None or dest_val is None:
                needs_update = True
                updated_row[col] = source_val
                continue
            
            # Both have values - compare them
            # Handle different numeric types (e.g., int vs float)
            try:
                if isinstance(source_val, (int, float)) and isinstance(dest_val, (int, float)):
                    if float(source_val) != float(dest_val):
                        needs_update = True
                        updated_row[col] = source_val
                elif source_val != dest_val:
                    needs_update = True
                    updated_row[col] = source_val
            except (TypeError, ValueError):
                # Fallback to direct comparison
                if source_val != dest_val:
                    needs_update = True
                    updated_row[col] = source_val
        
        if needs_update:
            rows_to_update.append(updated_row)
    
    return rows_to_update


def sync_em_all(conn_old, conn_new):
    """Main sync function for all or specified tables."""
    tables = [args.table] if args.table else get_all_tablez(conn_old)
    print(f"{colorize('Found', Colors.BLUE)} {colorize(len(tables), Colors.BOLD)}{colorize(' tables to process', Colors.BLUE)}")
    
    # Get optimal sync order based on FK dependencies
    if len(tables) > 1:
        print(f"\n{colorize('Analyzing foreign key dependencies...', Colors.CYAN)}")
        ordered_tables, circular_tables = get_sync_order(conn_old, tables)
        print(f"{colorize('Sync order:', Colors.CYAN)} {colorize(' -> '.join(ordered_tables), Colors.BOLD)}")
    else:
        ordered_tables = tables
        circular_tables = set()

    for table in ordered_tables:
        print(f"\n{colorize('Syncing:', Colors.BOLD + Colors.BLUE)} {colorize(table, Colors.BOLD + Colors.CYAN)}")
        pk = sniff_primary_key(conn_old, table)
        if not pk:
            print(f"  {colorize('WARNING:', Colors.YELLOW)} Skipping {table} (no PK found)")
            continue

        existing_old = count_rows(conn_old, table)
        existing_new_ids = pull_existing_ids(conn_new, table, pk)
        existing_new = len(existing_new_ids)

        # Detect schema differences and get common columns
        print(f"  {colorize('Analyzing schema...', Colors.CYAN)}")
        common_cols, missing_in_dest, missing_in_source, dest_cols = get_common_columns(conn_old, conn_new, table)
        
        if not common_cols:
            print(f"  {colorize('WARNING:', Colors.YELLOW)} No common columns found between source and destination for {table}")
            continue
            
        if pk not in common_cols:
            print(f"  {colorize('WARNING:', Colors.YELLOW)} Primary key '{pk}' not found in common columns for {table}")
            continue

        # Handle column-based sync if specified
        if args.columns:
            requested_cols = [col.strip() for col in args.columns.split(',')]
            # Ensure PK is always included
            if pk not in requested_cols:
                requested_cols.append(pk)
            # Filter to only include columns that exist in both tables
            sync_cols = [col for col in requested_cols if col in common_cols]
            if not sync_cols:
                print(f"  {colorize('WARNING:', Colors.YELLOW)} None of the requested columns exist in both tables for {table}")
                continue
            print(f"  {colorize('Syncing columns:', Colors.CYAN)} {', '.join(sync_cols)}")
        else:
            sync_cols = common_cols

        rows = pull_missing_rows(conn_old, table, pk, existing_new_ids, sync_cols)
        
        # Deep check: compare column values for existing rows
        rows_to_update = []
        dest_existing_rows = None
        if args.deep_check and existing_new_ids:
            print(f"  {colorize('Deep checking', Colors.MAGENTA)} {colorize(len(existing_new_ids), Colors.BOLD)} {colorize('existing rows for column differences...', Colors.MAGENTA)}")
            # Pull existing rows from both source and destination
            source_existing_rows = pull_existing_rows(conn_old, table, pk, existing_new_ids, sync_cols)
            dest_existing_rows = pull_existing_rows(conn_new, table, pk, existing_new_ids, sync_cols)
            
            # Compare and find differences
            rows_to_update = compare_and_find_differences(source_existing_rows, dest_existing_rows, pk, sync_cols)
            
            if rows_to_update:
                print(f"  {colorize('Found', Colors.YELLOW)} {colorize(len(rows_to_update), Colors.BOLD)} {colorize('rows with column differences to update', Colors.YELLOW)}")
            else:
                print(f"  {colorize('No column differences found in existing rows', Colors.GREEN)}")
        
        # Add default values for NOT NULL columns that are missing from source
        if rows:
            for row in rows:
                for col_name, col_info in dest_cols.items():
                    if col_name in common_cols and not col_info['nullable'] and col_name not in row:
                        # Provide smart defaults based on column type
                        if 'varchar' in col_info['type'] or 'text' in col_info['type']:
                            row[col_name] = f"migrated_{col_name}"
                        elif 'int' in col_info['type'] or 'numeric' in col_info['type']:
                            row[col_name] = 0
                        elif 'bool' in col_info['type']:
                            row[col_name] = False
                        else:
                            row[col_name] = col_info['default'] if col_info['default'] else f"migrated_{col_name}"
                        print(f"  {colorize('Added default value for', Colors.YELLOW)} {col_name}: {row[col_name]}")

        sync_log[table]["existing_old"] = existing_old
        sync_log[table]["existing_new"] = existing_new

        print(f"  {colorize('Old DB Rows:', Colors.BLUE)} {colorize(existing_old, Colors.BOLD)} {colorize('| New DB Rows (before):', Colors.BLUE)} {colorize(existing_new, Colors.BOLD)}")
        print(f"  {colorize(len(rows), Colors.BOLD)} {colorize('new rows to insert', Colors.GREEN)}")
        if args.deep_check:
            print(f"  {colorize(len(rows_to_update), Colors.BOLD)} {colorize('rows to update (deep check)', Colors.MAGENTA)}")

        try:
            is_circular = table in circular_tables
            # Update existing rows with different column values
            if rows_to_update:
                # Pass destination rows for before/after comparison in verbose mode
                # dest_existing_rows is defined in the deep_check block above
                dest_rows_for_comparison = dest_existing_rows if (args.deep_check and args.verbose and dest_existing_rows is not None) else None
                update_rows_in_new(conn_new, table, rows_to_update, pk, dest_rows=dest_rows_for_comparison, dry_run=args.dry_run, verbose=args.verbose, is_circular_fk=is_circular)
            # Insert new rows
            push_rows_to_new(conn_new, table, rows, pk, dry_run=args.dry_run, verbose=args.verbose, is_circular_fk=is_circular)
            print(f"  {colorize('Done with', Colors.GREEN)} {colorize(table, Colors.BOLD + Colors.GREEN)}")
        except Exception as e:
            print(f"  {colorize('ERROR:', Colors.RED + Colors.BOLD)} {colorize(f'Error syncing {table}:', Colors.RED)} {colorize(str(e), Colors.RED)}")
            # Rollback the failed transaction to prevent "aborted transaction" errors
            try:
                conn_new.rollback()
                print(f"  {colorize('Rolled back transaction for', Colors.YELLOW)} {table}")
            except Exception as rollback_error:
                print(f"  {colorize('WARNING:', Colors.YELLOW)} Rollback failed for {table}: {rollback_error}")
                # If rollback fails, we need to start a new connection
                try:
                    conn_new.close()
                    conn_new = psycopg2.connect(args.new_db_url)
                    print(f"  {colorize('Created new connection after rollback failure', Colors.CYAN)}")
                except Exception as reconnect_error:
                    print(f"  {colorize('ERROR:', Colors.RED + Colors.BOLD)} {colorize(f'Failed to reconnect: {reconnect_error}', Colors.RED)}")
                    break

    # === FINAL SYNC REPORT === #
    print(f"\n{colorize('=' * 60, Colors.CYAN)}")
    print(f"{colorize('Final Sync Report', Colors.BOLD + Colors.CYAN)}")
    print(f"{colorize('=' * 60, Colors.CYAN)}")
    for table, stats in sync_log.items():
        has_changes = stats["inserted"] > 0 or stats.get("updated", 0) > 0
        status_color = Colors.GREEN if has_changes else Colors.YELLOW
        status = "CHANGED" if has_changes else "UNCHANGED"
        print(f"\n{colorize('Table:', Colors.BOLD)} {colorize(table, Colors.CYAN)} {colorize('---', Colors.DIM)} {colorize(status, status_color + Colors.BOLD)}")
        print(f"   {colorize('Old DB Rows:', Colors.BLUE)} {stats['existing_old']}")
        print(f"   {colorize('New DB Rows (before):', Colors.BLUE)} {stats['existing_new']}")
        print(f"   {colorize('Rows Added:', Colors.GREEN)} {colorize(stats['inserted'], Colors.BOLD)}")
        if stats.get("updated", 0) > 0:
            print(f"   {colorize('Rows Updated:', Colors.MAGENTA)} {colorize(stats['updated'], Colors.BOLD)}")
        if stats["inserted_pks"]:
            print(f"   {colorize('PKs Added:', Colors.GREEN)} {stats['inserted_pks']}")
        if stats.get("updated_pks"):
            print(f"   {colorize('PKs Updated:', Colors.MAGENTA)} {stats['updated_pks']}")


# ===================== INSERT FUNCTIONALITY ===================== #

def parse_data_input(data_input: Optional[str] = None, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse data from JSON string, JSON file, or CSV file."""
    records = []
    
    if file_path:
        # Read from file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    records = [data]
                elif isinstance(data, list):
                    records = data
                else:
                    raise ValueError("JSON file must contain an object or array of objects")
        elif file_ext == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                records = list(reader)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Use .json or .csv")
    elif data_input:
        # Check if data_input is a file path
        if os.path.exists(data_input):
            # It's a file path, read it
            file_ext = os.path.splitext(data_input)[1].lower()
            if file_ext == '.json':
                with open(data_input, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        records = [data]
                    elif isinstance(data, list):
                        records = data
                    else:
                        raise ValueError("JSON file must contain an object or array of objects")
            elif file_ext == '.csv':
                with open(data_input, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}. Use .json or .csv")
        else:
            # Parse as JSON string
            try:
                data = json.loads(data_input)
                if isinstance(data, dict):
                    records = [data]
                elif isinstance(data, list):
                    records = data
                else:
                    raise ValueError("JSON data must be an object or array of objects")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
    else:
        raise ValueError("Either --data or --file must be provided")
    
    if not records:
        raise ValueError("No records found in input")
    
    return records


def validate_record_against_schema(conn, table_name: str, record: Dict[str, Any], columns: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and prepare a record for insertion."""
    validated = {}
    
    for col_name, col_info in columns.items():
        if col_name in record:
            value = record[col_name]
            # Convert empty strings to None for nullable columns
            if value == '' and col_info['nullable']:
                value = None
            validated[col_name] = value
        elif not col_info['nullable'] and col_info['default'] is None:
            # Required column without default
            raise ValueError(f"Required column '{col_name}' is missing and has no default value")
        # If column has default, we can skip it (PostgreSQL will use default)
    
    return validated


def insert_records(conn, table_name: str, records: List[Dict[str, Any]], 
                   dry_run: bool = False, verbose: bool = False, 
                   on_conflict: str = 'error', skip_fk: bool = False):
    """Insert records into a table gracefully."""
    if not records:
        print(f"{colorize('No records to insert', Colors.YELLOW)}")
        return
    
    # Get table schema
    columns = get_table_columns(conn, table_name)
    pk = sniff_primary_key(conn, table_name)
    
    if not columns:
        raise ValueError(f"Table '{table_name}' not found or has no columns")
    
    print(f"{colorize('Inserting', Colors.BLUE)} {colorize(len(records), Colors.BOLD)} {colorize('record(s) into table:', Colors.BLUE)} {colorize(table_name, Colors.CYAN)}")
    
    validated_records = []
    errors = []
    
    # Validate all records first
    for i, record in enumerate(records, 1):
        try:
            validated = validate_record_against_schema(conn, table_name, record, columns)
            validated_records.append(validated)
            if verbose:
                print(f"  {colorize(f'Record {i}:', Colors.CYAN)} {validated}")
        except Exception as e:
            error_msg = f"Record {i} validation failed: {e}"
            errors.append(error_msg)
            if verbose:
                print(f"  {colorize('ERROR:', Colors.RED)} {error_msg}")
            if not skip_fk:
                raise ValueError(error_msg)
    
    if errors and skip_fk:
        print(f"  {colorize(f'Skipped {len(errors)} invalid record(s)', Colors.YELLOW)}")
    
    if not validated_records:
        print(f"{colorize('No valid records to insert', Colors.YELLOW)}")
        return
    
    # Insert records
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    
    with conn.cursor() as cur:
        for i, record in enumerate(validated_records, 1):
            if dry_run:
                print(f"  {colorize(f'[DRY RUN] Would insert record {i}:', Colors.YELLOW)} {record}")
                continue
            
            # Adapt Python dict/list values (e.g., JSON/JSONB columns) for psycopg2
            def _adapt_value(value):
                if isinstance(value, (dict, list)):
                    return Json(value)
                return value
            
            # Build INSERT statement
            keys = list(record.keys())
            vals = [_adapt_value(record[k]) for k in keys]
            placeholders = ','.join(['%s'] * len(vals))
            columns_str = ','.join([quote_ident(k) for k in keys])
            
            try:
                if on_conflict == 'ignore':
                    # Use ON CONFLICT DO NOTHING
                    sql = f"INSERT INTO {quote_table(table_name)} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                    cur.execute(sql, vals)
                    if cur.rowcount > 0:
                        inserted_count += 1
                        if verbose:
                            print(f"  {colorize(f'Inserted record {i}:', Colors.GREEN)} {record}")
                    else:
                        skipped_count += 1
                        if verbose:
                            print(f"  {colorize(f'Skipped record {i} (conflict):', Colors.YELLOW)} {record}")
                elif on_conflict == 'update' and pk:
                    # Use ON CONFLICT DO UPDATE
                    update_cols = [k for k in keys if k != pk]
                    if update_cols:
                        update_clause = ', '.join([f"{quote_ident(k)} = EXCLUDED.{quote_ident(k)}" for k in update_cols])
                        sql = f"INSERT INTO {quote_table(table_name)} ({columns_str}) VALUES ({placeholders}) ON CONFLICT ({quote_ident(pk)}) DO UPDATE SET {update_clause}"
                        cur.execute(sql, vals)
                        if cur.rowcount > 0:
                            if record.get(pk) in [r.get(pk) for r in validated_records[:i-1]]:
                                updated_count += 1
                                if verbose:
                                    print(f"  {colorize(f'Updated record {i}:', Colors.MAGENTA)} {record}")
                            else:
                                inserted_count += 1
                                if verbose:
                                    print(f"  {colorize(f'Inserted record {i}:', Colors.GREEN)} {record}")
                    else:
                        # No columns to update, just ignore
                        sql = f"INSERT INTO {quote_table(table_name)} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        cur.execute(sql, vals)
                        if cur.rowcount > 0:
                            inserted_count += 1
                else:
                    # Default: error on conflict
                    sql = f"INSERT INTO {quote_table(table_name)} ({columns_str}) VALUES ({placeholders})"
                    cur.execute(sql, vals)
                    inserted_count += 1
                    if verbose:
                        print(f"  {colorize(f'Inserted record {i}:', Colors.GREEN)} {record}")
                        
            except psycopg2.IntegrityError as e:
                if skip_fk:
                    print(f"  {colorize(f'WARNING: Skipped record {i} due to constraint error:', Colors.YELLOW)} {e}")
                    skipped_count += 1
                else:
                    raise e
            except Exception as e:
                if skip_fk:
                    print(f"  {colorize(f'WARNING: Skipped record {i} due to error:', Colors.YELLOW)} {e}")
                    skipped_count += 1
                else:
                    raise e
    
    if not dry_run:
        conn.commit()
    
    # Summary
    print(f"\n{colorize('Insert Summary:', Colors.BOLD + Colors.CYAN)}")
    if not dry_run:
        print(f"  {colorize('Inserted:', Colors.GREEN)} {colorize(inserted_count, Colors.BOLD)}")
        if updated_count > 0:
            print(f"  {colorize('Updated:', Colors.MAGENTA)} {colorize(updated_count, Colors.BOLD)}")
        if skipped_count > 0:
            print(f"  {colorize('Skipped:', Colors.YELLOW)} {colorize(skipped_count, Colors.BOLD)}")
    else:
        print(f"  {colorize('[DRY RUN] Would insert:', Colors.YELLOW)} {colorize(len(validated_records), Colors.BOLD)} {colorize('record(s)', Colors.YELLOW)}")


def insert_em_all():
    """Main function for insert command."""
    try:
        # Parse data
        records = parse_data_input(args.data, args.file)
        
        # Connect to database
        conn = psycopg2.connect(args.db_url)
        
        try:
            insert_records(
                conn, 
                args.table, 
                records,
                dry_run=args.dry_run,
                verbose=args.verbose,
                on_conflict=args.on_conflict,
                skip_fk=args.skip_fk
            )
        finally:
            conn.close()
            
    except Exception as e:
        print(f"{colorize('ERROR:', Colors.RED + Colors.BOLD)} {colorize(str(e), Colors.RED)}")
        sys.exit(1)


# ===================== MAIN ===================== #
def main():
    if args.command == 'sync':
        conn_old = psycopg2.connect(args.old_db_url)
        conn_new = psycopg2.connect(args.new_db_url)

        try:
            sync_em_all(conn_old, conn_new)
        finally:
            conn_old.close()
            conn_new.close()
    
    elif args.command == 'insert':
        insert_em_all()
    
    else:
        print(f"{colorize('ERROR:', Colors.RED + Colors.BOLD)} Unknown command")
        sys.exit(1)
