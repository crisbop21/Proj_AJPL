---
name: inspect-schema
description: Use before making any database or schema-related changes. Inspects the current Supabase/PostgreSQL schema — tables, columns, types, constraints, triggers, and row counts.
---

# Inspect Database Schema

Run this skill to inspect the current state of the Supabase database schema before making any changes.

## Steps

1. Run the schema inspection script:
   ```
   python scripts/inspect_schema.py
   ```
   Optionally filter to a specific table:
   ```
   python scripts/inspect_schema.py --table clients
   python scripts/inspect_schema.py --table sessions
   ```

2. Compare the live schema against the expected schema documented in `CLAUDE.md` under "Database Schema (Supabase / PostgreSQL)".

3. Report any **drift** between the live schema and the documented schema:
   - Missing columns
   - Extra columns not in CLAUDE.md
   - Type mismatches
   - Missing triggers or functions

4. If the inspection script fails because `secrets.toml` is missing or Supabase is unreachable, fall back to reading the expected schema from `CLAUDE.md` and clearly state that you are showing the *documented* schema, not the live one.

## When to Use

- **Always** before modifying any database-related code in `services/database.py`
- **Always** before running `/modify-schema`
- When debugging data-related errors
- When adding new features that touch the database
