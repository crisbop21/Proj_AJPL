---
name: modify-schema
description: Use to modify the Supabase/PostgreSQL database schema. Always run /inspect-schema first. Handles ALTER TABLE, CREATE TABLE, triggers, functions, and other DDL changes with safety checks.
---

# Modify Database Schema

Run this skill to safely modify the Supabase database schema.

## Prerequisites

**CRITICAL**: Always run `/inspect-schema` first to understand the current state before making changes.

## Steps

1. **Inspect current schema** — Run `/inspect-schema` if not already done in this session.

2. **Write the migration SQL** — Based on the user's request, compose the appropriate SQL. Follow these patterns:

   - **Add a column**:
     ```sql
     ALTER TABLE table_name ADD COLUMN column_name TYPE DEFAULT default_value;
     ```
   - **Create a table**:
     ```sql
     CREATE TABLE table_name (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       ...
       created_at TIMESTAMPTZ DEFAULT NOW()
     );
     ```
   - **Add a trigger/function**: Follow the pattern of the existing `set_session_number` trigger in CLAUDE.md.
   - **Add a foreign key**:
     ```sql
     ALTER TABLE child_table ADD CONSTRAINT fk_name FOREIGN KEY (col) REFERENCES parent_table(id) ON DELETE CASCADE;
     ```

3. **Dry-run first** — Show the user what will happen:
   ```
   python scripts/modify_schema.py --dry-run --sql "YOUR SQL HERE"
   ```

4. **Ask for confirmation** — Always ask the user before executing destructive or irreversible changes. Show them:
   - The exact SQL to be executed
   - Any warnings from the validator
   - What tables/columns will be affected

5. **Execute the migration**:
   ```
   python scripts/modify_schema.py --yes --sql "YOUR SQL HERE"
   ```

6. **Verify** — Run `/inspect-schema` again to confirm the changes took effect.

7. **Update documentation** — If the schema changed:
   - Update the "Database Schema" section in `CLAUDE.md`
   - Update `services/database.py` if new functions are needed
   - Update or add tests in `tests/test_database.py`
   - Update `scripts/inspect_schema.py` expected schema if applicable

8. **Save migration** — For traceability, save the SQL to a migrations file:
   ```
   mkdir -p migrations
   ```
   Name format: `migrations/NNN_description.sql` (e.g., `migrations/001_add_email_to_clients.sql`)

## Safety Rules

- **NEVER** run DROP TABLE or DROP SCHEMA without explicit user confirmation
- **NEVER** modify the `id`, `client_id`, or `created_at` columns on existing tables
- **NEVER** drop the `set_session_number` trigger without providing a replacement
- **ALWAYS** use `IF NOT EXISTS` / `IF EXISTS` clauses when safe to do so
- **ALWAYS** include `ON DELETE CASCADE` for foreign keys referencing `clients(id)`
- **ALWAYS** run tests after schema changes to ensure nothing broke

## If the Script Fails

If `modify_schema.py` fails because the `run_sql` RPC function doesn't exist in Supabase:

1. Tell the user they need to create it in the Supabase SQL Editor:
   ```sql
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
   ```

2. Alternatively, provide the raw SQL and instruct the user to run it directly in the Supabase Dashboard SQL Editor.
