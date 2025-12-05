# Phase 5: 資料庫遷移

> **功能**: 日報時間過濾
> **階段**: Phase 5 of 5
> **狀態**: 完成
> **完成日期**: 2025-12-05

---

## 1. Planning (規劃)

### 1.1 目標

建立並執行資料庫遷移腳本，在現有 `daily_reports` 表中新增 `period_start` 和 `period_end` 欄位。

### 1.2 需求分析

**現有表結構:**
```sql
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**目標表結構:**
```sql
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    period_start DATETIME NOT NULL,     -- 新增
    period_end DATETIME NOT NULL,       -- 新增
    article_count INTEGER NOT NULL,
    top_articles TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 遷移策略

**SQLite 限制**: SQLite 不支援 `ALTER TABLE ... ADD COLUMN ... NOT NULL` 不帶預設值。

**解決方案**:
1. 先加入欄位 (nullable)
2. 更新現有記錄的欄位值
3. 不強制 NOT NULL (在應用層處理)

或使用備選方案:
1. 建立新表
2. 複製資料
3. 刪除舊表
4. 重新命名

**採用方案**: 方案 1 (較簡單，現有資料少)

### 1.4 影響範圍

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/memory/migrations/001_add_period_columns.py` | 新增 | 遷移腳本 |
| `src/memory/migrations/__init__.py` | 新增 | 遷移模組初始化 |

---

## 2. Implementation (實作)

### 2.1 建立遷移目錄

```
src/memory/migrations/
├── __init__.py
└── 001_add_period_columns.py
```

### 2.2 新增 __init__.py

**檔案**: `src/memory/migrations/__init__.py`

```python
"""
InsightCosmos Database Migrations

This module contains database migration scripts.

Usage:
    # Run a specific migration
    python -m src.memory.migrations.001_add_period_columns

    # Or import and run programmatically
    from src.memory.migrations.001_add_period_columns import migrate
    migrate()
"""
```

### 2.3 新增遷移腳本

**檔案**: `src/memory/migrations/001_add_period_columns.py`

```python
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
            print("✓ Column 'period_start' already exists")
        else:
            print("Adding column 'period_start'...")
            cursor.execute("""
                ALTER TABLE daily_reports
                ADD COLUMN period_start DATETIME
            """)
            print("✓ Column 'period_start' added")

        # Check and add period_end column
        if check_column_exists(cursor, 'daily_reports', 'period_end'):
            print("✓ Column 'period_end' already exists")
        else:
            print("Adding column 'period_end'...")
            cursor.execute("""
                ALTER TABLE daily_reports
                ADD COLUMN period_end DATETIME
            """)
            print("✓ Column 'period_end' added")

        # Add index for period_end (for efficient querying)
        print("Creating index on period_end...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_reports_period
                ON daily_reports(period_end DESC)
            """)
            print("✓ Index created")
        except sqlite3.OperationalError as e:
            if 'already exists' in str(e):
                print("✓ Index already exists")
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
            print(f"✓ Updated {null_count} record(s)")

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
```

---

## 3. Validation (驗證)

### 3.1 驗證項目

| 項目 | 驗證方法 | 預期結果 |
|------|----------|----------|
| 遷移腳本執行 | 手動執行 | 無錯誤 |
| 欄位新增 | SQL 查詢 | 欄位存在 |
| 冪等性 | 重複執行 | 不報錯 |
| 現有資料 | SQL 查詢 | 正確設定預設值 |
| 應用相容 | 整合測試 | 正常運作 |

### 3.2 測試步驟

```bash
# 1. 備份資料庫 (重要!)
cp data/insights.db data/insights.db.backup

# 2. 執行遷移
python -m src.memory.migrations.001_add_period_columns

# 3. 驗證欄位已新增
sqlite3 data/insights.db "PRAGMA table_info(daily_reports)"

# 4. 驗證索引已建立
sqlite3 data/insights.db ".indices daily_reports"

# 5. 驗證現有記錄已更新 (如果有的話)
sqlite3 data/insights.db "SELECT id, period_start, period_end FROM daily_reports"

# 6. 測試冪等性 (再次執行應無錯誤)
python -m src.memory.migrations.001_add_period_columns

# 7. 執行應用程式測試
python -m src.orchestrator.daily_runner --dry-run
```

### 3.3 預期輸出

```
Migration 001: Add period columns to daily_reports
Database: /Users/ray/sides/InsightCosmos/data/insights.db
--------------------------------------------------
Adding column 'period_start'...
✓ Column 'period_start' added
Adding column 'period_end'...
✓ Column 'period_end' added
Creating index on period_end...
✓ Index created

Found 0 existing record(s) with NULL period values.
--------------------------------------------------
Migration completed successfully!

Current daily_reports schema:
  id: INTEGER NOT NULL
  report_date: DATE NOT NULL
  period_start: DATETIME
  period_end: DATETIME
  article_count: INTEGER NOT NULL
  top_articles: TEXT NOT NULL
  content: TEXT NOT NULL
  sent_at: DATETIME
  created_at: DATETIME
```

### 3.4 驗收標準

- [x] 遷移腳本無錯誤執行 ✓
- [x] `period_start` 欄位已新增 ✓
- [x] `period_end` 欄位已新增 ✓
- [x] `idx_daily_reports_period` 索引已建立 ✓
- [x] 現有記錄有合理的預設值 ✓ (無既有記錄)
- [x] 重複執行不報錯 (冪等性) ✓
- [x] 應用程式正常運作 ✓

---

## 4. 回滾計畫

如果遷移出現問題:

### 方案 A: 還原備份

```bash
# 還原備份
cp data/insights.db.backup data/insights.db
```

### 方案 B: 保留欄位

新增的欄位即使不使用也不會影響現有功能，因為:
1. 欄位是 nullable
2. 現有程式碼不依賴這些欄位
3. 只有新功能會使用這些欄位

---

## 5. 相依性

**前置條件**:
- Phase 1 完成 (Schema 設計已確定) ✓

**後續步驟**:
- 所有 Phase 完成後，即可使用新的時間過濾功能 ✓

---

## 6. 部署檢查清單

- [x] 備份資料庫 ✓
- [x] 執行遷移腳本 ✓
- [x] 驗證欄位新增 ✓
- [x] 驗證索引建立 ✓
- [x] 執行應用程式測試 ✓
- [x] 更新文件 ✓

---

*完成日期: 2025-12-05*

*文件建立: 2025-12-05*
