"""Inspect the Supabase/PostgreSQL database schema.

Reads credentials from .streamlit/secrets.toml and queries
information_schema to show tables, columns, types, constraints,
triggers, and functions in the public schema.

Usage:
    python scripts/inspect_schema.py [--table TABLE_NAME]
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


def inspect_tables(supabase) -> list[dict]:
    """Get all tables in the public schema."""
    result = supabase.rpc("inspect_tables", {}).execute()
    return result.data


def inspect_full_schema(supabase, table_filter: str = None):
    """Query information_schema via RPC to get full schema details."""
    # Use the postgrest schema endpoint as fallback
    # Query columns via information_schema
    params = {}
    if table_filter:
        params["p_table_name"] = table_filter

    try:
        result = supabase.rpc("inspect_schema", params).execute()
        return result.data
    except Exception:
        # Fallback: use the REST API to describe tables
        return None


def print_schema_from_rest(supabase, table_filter: str = None):
    """Fallback: inspect schema by querying known tables directly."""
    tables = ["clients", "sessions"]
    if table_filter:
        tables = [t for t in tables if t == table_filter]

    for table_name in tables:
        print(f"\n{'='*60}")
        print(f"TABLE: {table_name}")
        print(f"{'='*60}")

        try:
            # Fetch one row to see column structure
            response = supabase.table(table_name).select("*").limit(0).execute()
            # The columns can be inferred from the response headers or schema
            # Try fetching a single row to see the shape
            sample = supabase.table(table_name).select("*").limit(1).execute()
            if sample.data:
                row = sample.data[0]
                print(f"\nColumns (inferred from data):")
                for col, val in row.items():
                    val_type = type(val).__name__ if val is not None else "unknown"
                    print(f"  - {col}: {val_type} (sample: {repr(val)[:80]})")
            else:
                print(f"  (table exists but is empty — cannot infer column types)")

            # Show row count
            count_resp = supabase.table(table_name).select("*", count="exact").limit(0).execute()
            print(f"\nRow count: {count_resp.count}")

        except Exception as e:
            print(f"  Error inspecting {table_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Inspect Supabase database schema")
    parser.add_argument("--table", "-t", help="Filter to a specific table name")
    args = parser.parse_args()

    secrets = load_secrets()
    supabase = get_client(secrets)

    print("=" * 60)
    print("SUPABASE DATABASE SCHEMA INSPECTION")
    print(f"URL: {secrets['SUPABASE_URL']}")
    print("=" * 60)

    # Try the RPC approach first
    schema_data = inspect_full_schema(supabase, args.table)

    if schema_data:
        for item in schema_data:
            print(item)
    else:
        # Fallback to REST-based inspection
        print("\n(Using REST API fallback — for full schema details,")
        print(" create the inspect_schema RPC function in Supabase.)\n")
        print_schema_from_rest(supabase, args.table)

    # Always print the expected schema from CLAUDE.md for reference
    print(f"\n{'='*60}")
    print("EXPECTED SCHEMA (from CLAUDE.md)")
    print(f"{'='*60}")
    print("""
TABLE: clients
  - id:         UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - name:       TEXT NOT NULL
  - notes:      TEXT
  - created_at: TIMESTAMPTZ DEFAULT NOW()

TABLE: sessions
  - id:                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - client_id:           UUID REFERENCES clients(id) ON DELETE CASCADE
  - raw_transcript:      TEXT
  - structured_summary:  JSONB
  - session_number:      INT (auto-set by trigger)
  - recorded_at:         TIMESTAMPTZ DEFAULT NOW()

TRIGGER: auto_session_number
  BEFORE INSERT ON sessions
  Sets session_number = MAX(session_number) + 1 per client_id

FUNCTION: set_session_number()
  Used by auto_session_number trigger
""")


if __name__ == "__main__":
    main()
