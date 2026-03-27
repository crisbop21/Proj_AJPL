"""Modify the Supabase/PostgreSQL database schema.

Reads credentials from .streamlit/secrets.toml and executes SQL
statements against the database via Supabase RPC.

SAFETY: Always run inspect_schema.py first to understand current state.
This script requires explicit confirmation before executing.

Usage:
    python scripts/modify_schema.py --sql "ALTER TABLE clients ADD COLUMN email TEXT;"
    python scripts/modify_schema.py --file migrations/001_add_email.sql
    python scripts/modify_schema.py --dry-run --sql "ALTER TABLE clients ADD COLUMN email TEXT;"
"""

import argparse
import sys
import tomllib
from pathlib import Path
from supabase import create_client


def load_secrets() -> dict:
    """Load secrets from .streamlit/secrets.toml."""
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"ERROR: {secrets_path} not found. Create it with your Supabase credentials.")
        sys.exit(1)
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def get_client(secrets: dict):
    """Create Supabase client from secrets."""
    return create_client(secrets["SUPABASE_URL"], secrets["SUPABASE_ANON_KEY"])


def validate_sql(sql: str) -> list[str]:
    """Basic validation of SQL statements. Returns list of warnings."""
    warnings = []
    sql_upper = sql.upper().strip()

    # Check for dangerous operations
    if "DROP TABLE" in sql_upper:
        warnings.append("WARNING: DROP TABLE detected — this will permanently delete the table and all its data!")
    if "DROP SCHEMA" in sql_upper:
        warnings.append("DANGER: DROP SCHEMA detected — this could destroy the entire schema!")
    if "TRUNCATE" in sql_upper:
        warnings.append("WARNING: TRUNCATE detected — this will delete all rows in the table!")
    if "DELETE FROM" in sql_upper and "WHERE" not in sql_upper:
        warnings.append("WARNING: DELETE without WHERE clause — this will delete ALL rows!")
    if "DROP COLUMN" in sql_upper:
        warnings.append("WARNING: DROP COLUMN detected — existing data in this column will be lost!")
    if "DROP FUNCTION" in sql_upper:
        warnings.append("WARNING: DROP FUNCTION detected — triggers depending on this function will break!")
    if "DROP TRIGGER" in sql_upper:
        warnings.append("WARNING: DROP TRIGGER detected — auto-increment behavior may be affected!")

    return warnings


def execute_sql(supabase, sql: str) -> dict:
    """Execute SQL via Supabase RPC.

    Requires a 'run_sql' function in Supabase:

    CREATE OR REPLACE FUNCTION run_sql(query text)
    RETURNS json AS $$
    DECLARE
        result json;
    BEGIN
        EXECUTE query;
        RETURN json_build_object('success', true, 'message', 'Query executed successfully');
    EXCEPTION WHEN OTHERS THEN
        RETURN json_build_object('success', false, 'error', SQLERRM, 'detail', SQLSTATE);
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    try:
        result = supabase.rpc("run_sql", {"query": sql}).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Modify Supabase database schema")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sql", "-s", help="SQL statement to execute")
    group.add_argument("--file", "-f", help="Path to .sql file to execute")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="Show what would be executed without running it")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")
    args = parser.parse_args()

    # Load SQL
    if args.file:
        sql_path = Path(args.file)
        if not sql_path.exists():
            print(f"ERROR: File not found: {sql_path}")
            sys.exit(1)
        sql = sql_path.read_text()
    else:
        sql = args.sql

    sql = sql.strip()
    if not sql:
        print("ERROR: Empty SQL statement.")
        sys.exit(1)

    print("=" * 60)
    print("SUPABASE SCHEMA MODIFICATION")
    print("=" * 60)
    print(f"\nSQL to execute:\n")
    print(f"  {sql}")
    print()

    # Validate
    warnings = validate_sql(sql)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  {w}")
        print()

    if args.dry_run:
        print("[DRY RUN] No changes were made.")
        return

    # Confirm
    if not args.yes:
        response = input("Execute this SQL? (yes/no): ").strip().lower()
        if response != "yes":
            print("Aborted.")
            sys.exit(0)

    # Execute
    secrets = load_secrets()
    supabase = get_client(secrets)

    print("Executing...")
    result = execute_sql(supabase, sql)

    if result["success"]:
        print(f"\nSUCCESS: {result.get('data', 'Query executed.')}")
    else:
        print(f"\nFAILED: {result['error']}")
        sys.exit(1)

    print("\nNOTE: Run 'python scripts/inspect_schema.py' to verify the changes.")
    print("NOTE: Update CLAUDE.md if the schema definition has changed.")


if __name__ == "__main__":
    main()
