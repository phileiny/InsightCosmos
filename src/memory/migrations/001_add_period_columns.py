"""
Migration 001: Add period_start and period_end to daily_reports

This migration adds time period tracking columns to the daily_reports table.

Columns added:
    - period_start: Article collection start time
    - period_end: Article collection end time

Usage:
    python -m src.memory.migrations.001_add_period_columns

Note:
    - This migration is idempotent (safe to run multiple times)
    - Existing records will have NULL values for the new columns
    - The application should handle NULL values gracefully
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def get_db_path() -> Path:
    """Get the database file path"""
    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / 'data' / 'insights.db',
        Path.cwd() / 'data' / 'insights.db',
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Default path (will be created if running from project root)
    return possible_paths[0]


def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns


def migrate(db_path: Path = None) -> bool:
    """
    Run the migration

    Args:
        db_path: Path to the database file (optional, auto-detected if not provided)

    Returns:
        bool: True if migration successful, False otherwise
    """
    if db_path is None:
        db_path = get_db_path()

    print(f"Migration 001: Add period columns to daily_reports")
    print(f"Database: {db_path}")
    print("-" * 50)

    if not db_path.exists():
        print(f"ERROR: Database file not found: {db_path}")
        print("Please run the application first to create the database.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='daily_reports'
        """)
        if not cursor.fetchone():
            print("Table 'daily_reports' does not exist.")
            print("This is normal for a new database - the table will be created with the new schema.")
            conn.close()
            return True

        # Check and add period_start column
        if check_column_exists(cursor, 'daily_reports', 'period_start'):
            print("  Column 'period_start' already exists")
        else:
            print("Adding column 'period_start'...")
            cursor.execute("""
                ALTER TABLE daily_reports
                ADD COLUMN period_start DATETIME
            """)
            print("  Column 'period_start' added")

        # Check and add period_end column
        if check_column_exists(cursor, 'daily_reports', 'period_end'):
            print("  Column 'period_end' already exists")
        else:
            print("Adding column 'period_end'...")
            cursor.execute("""
                ALTER TABLE daily_reports
                ADD COLUMN period_end DATETIME
            """)
            print("  Column 'period_end' added")

        # Add index for period_end (for efficient querying)
        print("Creating index on period_end...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_reports_period
                ON daily_reports(period_end DESC)
            """)
            print("  Index created")
        except sqlite3.OperationalError as e:
            if 'already exists' in str(e):
                print("  Index already exists")
            else:
                raise

        # Update existing records with default values (optional)
        cursor.execute("SELECT COUNT(*) FROM daily_reports WHERE period_start IS NULL")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"\nFound {null_count} existing record(s) with NULL period values.")
            print("Setting default values based on created_at...")

            # Set period_end to created_at, period_start to created_at - 1 day
            cursor.execute("""
                UPDATE daily_reports
                SET period_end = created_at,
                    period_start = datetime(created_at, '-1 day')
                WHERE period_start IS NULL
            """)
            print(f"  Updated {null_count} record(s)")

        conn.commit()

        print("-" * 50)
        print("Migration completed successfully!")

        # Show current schema
        print("\nCurrent daily_reports schema:")
        cursor.execute("PRAGMA table_info(daily_reports)")
        for col in cursor.fetchall():
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else ''}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()


def rollback(db_path: Path = None) -> bool:
    """
    Rollback the migration (remove added columns)

    Note: SQLite doesn't support DROP COLUMN directly.
    This function documents the rollback steps but requires manual intervention.

    Args:
        db_path: Path to the database file

    Returns:
        bool: True if rollback info displayed
    """
    print("Rollback Migration 001")
    print("-" * 50)
    print("SQLite does not support DROP COLUMN directly.")
    print("To rollback, you would need to:")
    print("1. Create a new table without the columns")
    print("2. Copy data from old table")
    print("3. Drop old table")
    print("4. Rename new table")
    print("")
    print("However, keeping the columns is harmless - they will simply be NULL")
    print("for any pre-migration records.")
    print("")
    print("If you really need to rollback, use:")
    print("  sqlite3 data/insights.db")
    print("  CREATE TABLE daily_reports_new AS SELECT id, report_date, ...")
    print("  DROP TABLE daily_reports;")
    print("  ALTER TABLE daily_reports_new RENAME TO daily_reports;")

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migration 001: Add period columns')
    parser.add_argument('--rollback', action='store_true', help='Show rollback instructions')
    parser.add_argument('--db', type=str, help='Database file path')

    args = parser.parse_args()

    if args.rollback:
        rollback(Path(args.db) if args.db else None)
    else:
        db_path = Path(args.db) if args.db else None
        success = migrate(db_path)
        sys.exit(0 if success else 1)
