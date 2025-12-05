# Phase 3: 修改 ArticleStore 時間過濾

> **功能**: 日報時間過濾
> **階段**: Phase 3 of 5
> **狀態**: 規劃中

---

## 1. Planning (規劃)

### 1.1 目標

修改 `ArticleStore.get_top_priority()` 方法，加入 `fetched_after` 和 `fetched_before` 參數，支援依時間範圍篩選文章。

### 1.2 需求分析

**現有方法簽名:**
```python
def get_top_priority(
    self,
    limit: int = 10,
    status: Optional[str] = None
) -> List[Dict[str, Any]]
```

**問題**: 無法限制文章的收集時間，導致舊文章重複出現在日報中。

### 1.3 設計規格

**新方法簽名:**
```python
def get_top_priority(
    self,
    limit: int = 10,
    status: Optional[str] = None,
    fetched_after: Optional[datetime] = None,   # 新增
    fetched_before: Optional[datetime] = None   # 新增
) -> List[Dict[str, Any]]
```

**參數說明:**

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `limit` | int | 10 | 最大回傳數量 |
| `status` | Optional[str] | None | 狀態過濾 |
| `fetched_after` | Optional[datetime] | None | 只取此時間之後收集的文章 |
| `fetched_before` | Optional[datetime] | None | 只取此時間之前收集的文章 |

**SQL 邏輯變化:**

```sql
-- 修改前
SELECT * FROM articles
WHERE status = 'analyzed'
  AND priority_score IS NOT NULL
ORDER BY priority_score DESC
LIMIT 30;

-- 修改後
SELECT * FROM articles
WHERE status = 'analyzed'
  AND priority_score IS NOT NULL
  AND fetched_at > :fetched_after      -- 新增
  AND fetched_at <= :fetched_before    -- 新增
ORDER BY priority_score DESC
LIMIT 30;
```

### 1.4 影響範圍

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `src/memory/article_store.py` | 修改 | 更新 get_top_priority() 方法 |

### 1.5 向後相容性

- 新參數皆為 Optional，預設值為 None
- 當參數為 None 時，行為與原本相同
- 現有呼叫不需修改即可正常運作

---

## 2. Implementation (實作)

### 2.1 修改 article_store.py

**檔案**: `src/memory/article_store.py`

**修改位置**: `get_top_priority()` 方法 (約 Lines 250-280)

```python
def get_top_priority(
    self,
    limit: int = 10,
    status: Optional[str] = None,
    fetched_after: Optional[datetime] = None,
    fetched_before: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Get top priority articles with optional time filtering

    Args:
        limit: Maximum number of results (default: 10)
        status: Filter by status (optional)
        fetched_after: Only include articles fetched AFTER this time (exclusive)
        fetched_before: Only include articles fetched BEFORE or AT this time (inclusive)

    Returns:
        List[dict]: List of articles ordered by priority score (descending)

    Example:
        >>> # 取所有高優先度文章 (原有用法，向後相容)
        >>> articles = store.get_top_priority(limit=10, status='analyzed')

        >>> # 取特定時間範圍內的文章 (新用法)
        >>> from datetime import datetime, timedelta
        >>> period_start = datetime.utcnow() - timedelta(days=1)
        >>> period_end = datetime.utcnow()
        >>> articles = store.get_top_priority(
        ...     limit=30,
        ...     status='analyzed',
        ...     fetched_after=period_start,
        ...     fetched_before=period_end
        ... )
    """
    try:
        with self.database.get_session() as session:
            query = session.query(Article).filter(
                Article.priority_score.isnot(None)
            )

            # 狀態過濾
            if status:
                query = query.filter(Article.status == status)

            # 時間範圍過濾 (新增)
            if fetched_after is not None:
                query = query.filter(Article.fetched_at > fetched_after)
                self.logger.debug(f"Filtering articles fetched after: {fetched_after}")

            if fetched_before is not None:
                query = query.filter(Article.fetched_at <= fetched_before)
                self.logger.debug(f"Filtering articles fetched before: {fetched_before}")

            # 排序和限制
            query = query.order_by(desc(Article.priority_score))
            query = query.limit(limit)

            articles = query.all()

            self.logger.info(
                f"get_top_priority: found {len(articles)} articles "
                f"(limit={limit}, status={status}, "
                f"after={fetched_after}, before={fetched_before})"
            )

            return [article.to_dict() for article in articles]

    except Exception as e:
        self.logger.error(f"Failed to get top priority articles: {e}")
        raise
```

---

## 3. Validation (驗證)

### 3.1 驗證項目

| 項目 | 驗證方法 | 預期結果 |
|------|----------|----------|
| 向後相容 | 現有測試 | 不傳新參數時行為不變 |
| fetched_after 過濾 | 單元測試 | 只回傳該時間之後的文章 |
| fetched_before 過濾 | 單元測試 | 只回傳該時間之前的文章 |
| 組合過濾 | 單元測試 | 正確回傳時間範圍內的文章 |
| 空結果處理 | 單元測試 | 回傳空列表 |

### 3.2 測試案例

```python
# tests/unit/test_article_store_time_filter.py

import pytest
from datetime import datetime, timedelta
from src.memory.article_store import ArticleStore
from src.memory.database import Database


@pytest.fixture
def article_store_with_data(tmp_path):
    """建立測試用 ArticleStore 並插入測試資料"""
    db_path = tmp_path / "test.db"
    db = Database(f"sqlite:///{db_path}")
    db.create_tables()
    store = ArticleStore(db)

    # 插入測試文章
    now = datetime.utcnow()

    # 3 天前的文章
    store.create(
        url="https://example.com/old",
        title="Old Article",
        source="test"
    )
    # 手動更新 fetched_at
    store.update(1, fetched_at=now - timedelta(days=3), priority_score=0.9, status='analyzed')

    # 1 天前的文章
    store.create(
        url="https://example.com/recent",
        title="Recent Article",
        source="test"
    )
    store.update(2, fetched_at=now - timedelta(days=1), priority_score=0.8, status='analyzed')

    # 今天的文章
    store.create(
        url="https://example.com/today",
        title="Today Article",
        source="test"
    )
    store.update(3, fetched_at=now, priority_score=0.7, status='analyzed')

    return store, now


class TestArticleStoreTimeFilter:

    def test_backward_compatible_no_filter(self, article_store_with_data):
        """測試不傳時間參數時，回傳所有文章 (向後相容)"""
        store, _ = article_store_with_data

        articles = store.get_top_priority(limit=10, status='analyzed')

        assert len(articles) == 3

    def test_fetched_after_filter(self, article_store_with_data):
        """測試 fetched_after 過濾"""
        store, now = article_store_with_data

        # 只取 2 天內的文章
        cutoff = now - timedelta(days=2)
        articles = store.get_top_priority(
            limit=10,
            status='analyzed',
            fetched_after=cutoff
        )

        assert len(articles) == 2
        # 不應包含 3 天前的文章
        urls = [a['url'] for a in articles]
        assert 'https://example.com/old' not in urls

    def test_fetched_before_filter(self, article_store_with_data):
        """測試 fetched_before 過濾"""
        store, now = article_store_with_data

        # 只取 2 天前的文章
        cutoff = now - timedelta(days=2)
        articles = store.get_top_priority(
            limit=10,
            status='analyzed',
            fetched_before=cutoff
        )

        assert len(articles) == 1
        assert articles[0]['url'] == 'https://example.com/old'

    def test_combined_filter(self, article_store_with_data):
        """測試組合過濾 (時間範圍)"""
        store, now = article_store_with_data

        # 取 2 天前到 12 小時前的文章
        after = now - timedelta(days=2)
        before = now - timedelta(hours=12)

        articles = store.get_top_priority(
            limit=10,
            status='analyzed',
            fetched_after=after,
            fetched_before=before
        )

        assert len(articles) == 1
        assert articles[0]['url'] == 'https://example.com/recent'

    def test_empty_result(self, article_store_with_data):
        """測試無符合條件時回傳空列表"""
        store, now = article_store_with_data

        # 未來時間，不應有任何文章
        future = now + timedelta(days=1)
        articles = store.get_top_priority(
            limit=10,
            status='analyzed',
            fetched_after=future
        )

        assert len(articles) == 0

    def test_priority_order_preserved(self, article_store_with_data):
        """測試仍按優先度排序"""
        store, now = article_store_with_data

        articles = store.get_top_priority(
            limit=10,
            status='analyzed',
            fetched_after=now - timedelta(days=2)
        )

        # 應按 priority_score 降序
        scores = [a['priority_score'] for a in articles]
        assert scores == sorted(scores, reverse=True)
```

### 3.3 驗收標準

- [x] `get_top_priority()` 新增 `fetched_after`, `fetched_before` 參數 ✓
- [x] 不傳新參數時行為與原本相同 (向後相容) ✓
- [x] `fetched_after` 正確過濾 (排除該時間之前的文章) ✓
- [x] `fetched_before` 正確過濾 (排除該時間之後的文章) ✓
- [x] 組合使用時正確過濾時間範圍 ✓
- [x] 結果仍按 `priority_score` 降序排列 ✓
- [x] 單元測試全部通過 ✓

---

## 4. 相依性

**前置條件**: 無 (可獨立實作)

**後續階段**:
- Phase 4 (CuratorDailyRunner) 將呼叫此方法的新參數

---

*文件建立: 2025-12-05*
*完成日期: 2025-12-05*
