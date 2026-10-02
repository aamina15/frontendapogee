#!/usr/bin/env python3
"""
Phase 1 Migration: Add `format` column to resources table.

Idempotent, non-destructive, preserves all existing data.
Run once on any database (SQLite or PostgreSQL) before deploying Phase 1 code.

Usage:
    python -m migrations.add_format_column
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apogee.db")

engine = create_engine(DATABASE_URL)

def column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns

def run_migration():
    """Add format column if missing."""
    with engine.connect() as conn:
        # Check if table exists
        inspector = inspect(engine)
        if "resources" not in inspector.get_table_names():
            print("✓ Table 'resources' does not exist yet - will be created by SQLAlchemy on startup")
            return

        # Check if format column exists
        if column_exists(engine, "resources", "format"):
            print("✓ Column 'format' already exists - no migration needed")
            return

        # Add the column
        print("→ Adding 'format' column to resources table...")
        try:
            # SQLite and PostgreSQL both support this syntax for nullable column
            conn.execute(text("ALTER TABLE resources ADD COLUMN format TEXT"))
            conn.commit()
            print("✓ Column 'format' added successfully")
        except Exception as e:
            # Handle edge case where column was added concurrently
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("✓ Column 'format' already exists (concurrent add)")
            else:
                print(f"✗ Migration failed: {e}")
                raise

def backfill_formats():
    """Optional: backfill format for existing resources based on catalogue.
    Only runs if format column exists but has NULL values.
    """
    from services.resource_service import VERIFIED_RESOURCE_CATALOGUE, VERIFIED_VIDEO_CATALOGUE, _KEYWORD_ALIASES, find_verified_resource_for_skill

    with engine.connect() as conn:
        # Check if there are resources with NULL format
        result = conn.execute(text("SELECT COUNT(*) FROM resources WHERE format IS NULL"))
        null_count = result.scalar()

        if null_count == 0:
            print("✓ All resources already have format set")
            return

        print(f"→ Backfilling format for {null_count} resources...")

        # Get all resources with NULL format
        result = conn.execute(text("""
            SELECT r.id, r.skill_id, r.title, s.name as skill_name, s.slug
            FROM resources r
            JOIN skills s ON r.skill_id = s.id
            WHERE r.format IS NULL
        """))

        updated = 0
        for row in result:
            resource_id = row.id
            skill_name = row.skill_name
            skill_slug = row.slug or ""

            # Look up in catalogue
            reading_entry = find_verified_resource_for_skill(skill_name, skill_slug)

            if reading_entry:
                # Determine format from catalogue entry
                fmt = reading_entry.get("format", "reading")
                conn.execute(
                    text("UPDATE resources SET format = :fmt WHERE id = :id"),
                    {"fmt": fmt, "id": resource_id}
                )
                updated += 1

        conn.commit()
        print(f"✓ Backfilled format for {updated} resources")

if __name__ == "__main__":
    print(f"Phase 1 Migration: Add 'format' column to resources")
    print(f"Database: {DATABASE_URL}")
    print("-" * 50)

    run_migration()
    backfill_formats()

    print("-" * 50)
    print("Migration complete ✓")