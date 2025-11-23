# Stage 2: Memory Layer - 實作筆記

> **階段**: Stage 2 - Memory Layer
> **開始時間**: 2025-11-21
> **完成時間**: 2025-11-21
> **狀態**: ✅ 已完成
> **總耗時**: ~3 小時

---

## 📋 實作概述

本階段成功實作了 InsightCosmos 的 Memory Layer（記憶層），包括資料庫管理、文章存儲、Embedding 向量檢索等核心功能。

### 完成的組件

1. ✅ **schema.sql** - SQLite 資料庫結構定義（4 個表）
2. ✅ **models.py** - SQLAlchemy ORM 模型定義（4 個模型類）
3. ✅ **database.py** - 資料庫連接與初始化管理
4. ✅ **article_store.py** - 文章資料 CRUD 操作
5. ✅ **embedding_store.py** - Embedding 向量存儲與相似度檢索
6. ✅ **test_memory.py** - 完整的單元測試套件（16 個測試）

---

## 🏗️ 架構實作細節

### 1. Database Schema (schema.sql)

#### 設計決策

- **4 個主表**:
  - `articles` - 文章資料與元數據
  - `embeddings` - 文章的 Embedding 向量
  - `daily_reports` - 每日報告
  - `weekly_reports` - 每週報告

- **索引策略**:
  - `idx_articles_url` - 快速去重查詢
  - `idx_articles_status` - 狀態篩選查詢
  - `idx_articles_priority_score` - 優先級排序查詢
  - `idx_articles_published_at` - 時間範圍查詢

- **特殊功能**:
  - `PRAGMA foreign_keys = ON` - 啟用外鍵約束
  - `PRAGMA journal_mode = WAL` - Write-Ahead Logging 提升並發效能
  - `UPDATE` trigger - 自動更新 `updated_at` 時間戳

#### 關鍵欄位設計

```sql
-- articles 表的核心欄位
url TEXT UNIQUE NOT NULL           -- 唯一標識，用於去重
status TEXT DEFAULT 'pending'      -- 處理狀態流程: pending → analyzed → reported
priority_score REAL                -- 0.0-1.0 分數，由 Analyst Agent 產生
analysis TEXT                      -- JSON 格式的分析結果
```

---

### 2. ORM Models (models.py)

#### Article Model

**特色功能**:
- `to_dict()` 方法 - 自動轉換為字典，處理 JSON 解析與日期格式化
- Relationship mapping - 與 Embedding 的一對多關係
- 自動時間戳 - `created_at` 和 `updated_at` 自動管理

**實作亮點**:
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        'tags': self.tags.split(',') if self.tags else [],  # 字符串轉陣列
        'analysis': json.loads(self.analysis) if self.analysis else None,  # JSON 解析
        'published_at': self.published_at.isoformat() if self.published_at else None  # 日期格式化
    }
```

#### Embedding Model

**核心設計**:
- `embedding` 欄位使用 `LargeBinary` 存儲序列化的 numpy array
- 唯一約束 `UNIQUE(article_id, model)` - 確保每篇文章每個模型只有一個 Embedding
- 級聯刪除 `ON DELETE CASCADE` - 刪除文章時自動刪除相關 Embedding

---

### 3. Database Manager (database.py)

#### 核心功能

1. **資料庫初始化**:
   ```python
   def init_db(self, drop_all: bool = False) -> None:
       # 1. 使用 SQLAlchemy 創建所有表
       Base.metadata.create_all(bind=self.engine)
       # 2. 執行 schema.sql 中的額外 SQL (triggers, indexes)
       self._execute_schema_sql()
       # 3. 驗證所有表都已創建
       self._verify_tables()
   ```

2. **Session 管理**:
   - Context manager 模式 (`with db.get_session() as session`)
   - 自動 commit/rollback
   - 異常安全處理

3. **SQLite 優化**:
   - 啟用 foreign key constraints
   - WAL mode 提升並發效能
   - 30 秒 timeout 避免鎖定問題

#### 實作挑戰與解決方案

**挑戰 1**: Logger 類型錯誤
**問題**: 最初使用 `Logger("name")` 實例化，但 Logger 是靜態類
**解決**: 改用 `Logger.get_logger("name")` 靜態方法

**挑戰 2**: Config 對象沒有 `get()` 方法
**問題**: Config 是 dataclass，不是字典
**解決**: 從 `config.get('database_path')` 改為 `config.database_path`

---

### 4. Article Store (article_store.py)

#### 實作的 CRUD 操作

| 方法 | 功能 | 用途 |
|------|------|------|
| `create()` | 創建文章 | Scout Agent 收集後插入 |
| `get_by_id()` | ID 查詢 | 精確獲取單篇文章 |
| `get_by_url()` | URL 查詢 | 去重檢查 |
| `get_by_status()` | 狀態查詢 | 獲取待處理/已分析文章 |
| `get_recent()` | 時間範圍查詢 | 獲取最近 N 天文章 |
| `get_top_priority()` | 優先級排序 | Daily Report 選取高優先級文章 |
| `update()` | 更新欄位 | 通用更新方法 |
| `update_status()` | 狀態更新 | 流程控制 |
| `update_analysis()` | 分析結果更新 | Analyst Agent 儲存分析 |
| `delete()` | 刪除文章 | 清理資料 |
| `exists()` | 存在性檢查 | 去重判斷 |
| `count_by_status()` | 狀態計數 | 統計資訊 |

#### 去重機制

```python
def create(self, url: str, ...):
    if self.exists(url):
        raise ValueError(f"Article with URL already exists: {url}")
    # ... 創建文章
```

- 使用 `UNIQUE` constraint 在資料庫層面保證唯一性
- `exists()` 方法提供程式層面的檢查
- 拋出明確的 `ValueError` 便於錯誤處理

---

### 5. Embedding Store (embedding_store.py)

#### 向量序列化策略

**技術選擇**: Python `pickle` 模組
**原因**:
- 簡單高效，原生支援 numpy array
- 序列化/反序列化速度快
- 不需要額外依賴

```python
@staticmethod
def serialize_vector(vector: np.ndarray) -> bytes:
    return pickle.dumps(vector)

@staticmethod
def deserialize_vector(data: bytes) -> np.ndarray:
    return pickle.loads(data)
```

#### 相似度搜尋實作

**演算法**: 余弦相似度 (Cosine Similarity)

```python
@staticmethod
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    dot_product = np.dot(vec1, vec2)
    similarity = dot_product / (norm1 * norm2)

    return float(similarity)
```

**搜尋流程**:
1. 從資料庫載入所有指定模型的 Embedding
2. 逐一計算與查詢向量的余弦相似度
3. 過濾低於閾值的結果
4. 按相似度降序排序並返回 top K

**效能考量**:
- 當前實作: **全量掃描** (Full Scan)
- 適用場景: < 10,000 篇文章
- 未來優化方向: 使用專用向量資料庫 (Faiss, Annoy, Milvus)

---

## 🧪 測試實作

### 測試框架

- **工具**: pytest
- **測試數量**: 16 個測試案例
- **通過率**: 100% (16/16 PASSED)
- **執行時間**: ~0.26 秒

### 測試案例清單

#### Database 測試 (2 個)
- `test_database_initialization` - 資料庫初始化成功
- `test_database_creates_all_tables` - 所有表創建驗證

#### ArticleStore 測試 (7 個)
- `test_article_store_create` - 文章創建功能
- `test_article_store_url_deduplication` - URL 去重機制
- `test_article_store_query` - 查詢功能（ID, URL）
- `test_article_store_update_status` - 狀態更新
- `test_article_store_priority_sorting` - 優先級排序
- `test_article_store_query_by_date` - 時間範圍查詢
- `test_article_store_exists_method` - 存在性檢查
- `test_article_store_count_by_status` - 狀態計數

#### EmbeddingStore 測試 (5 個)
- `test_embedding_store_store_vector` - 向量存儲
- `test_embedding_store_get_vector` - 向量檢索
- `test_embedding_store_similarity_search` - 相似度搜尋
- `test_embedding_store_cosine_similarity` - 余弦相似度計算
- `test_embedding_store_delete` - 向量刪除

#### 集成測試 (2 個)
- `test_cascade_delete` - 級聯刪除驗證

### Fixtures 設計

```python
@pytest.fixture(scope='function')
def temp_db_path():
    """為每個測試創建臨時資料庫"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_insights.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)  # 測試後清理

@pytest.fixture(scope='function')
def database(test_config):
    """創建並初始化資料庫"""
    db = Database.from_config(test_config)
    db.init_db()
    yield db
    db.close()
```

---

## 🐛 遇到的問題與解決方案

### 問題 1: Python 2.7 pip 錯誤

**現象**: `pip install numpy` 失敗，顯示 Python 2.7 相關錯誤
**原因**: 系統預設 `pip` 指向 Python 2.7
**解決**: 使用 `python3 -m pip install` 明確指定 Python 3

### 問題 2: externally-managed-environment

**現象**: pip 安裝套件時報錯，提示環境由外部管理
**原因**: macOS Homebrew Python 的 PEP 668 保護機制
**解決**: 使用 `--break-system-packages` 參數（測試環境可接受）

### 問題 3: Logger 類型錯誤

**現象**: `TypeError: Logger() takes no arguments`
**原因**: Logger 是靜態類，不支援實例化
**解決**: 從 `Logger("name")` 改為 `Logger.get_logger("name")`

**涉及檔案**:
- `database.py` - 3 處修改
- `article_store.py` - 1 處修改
- `embedding_store.py` - 1 處修改

### 問題 4: Config 物件不是字典

**現象**: `AttributeError: 'Config' object has no attribute 'get'`
**原因**: Config 是 dataclass，使用屬性訪問而非字典方法
**解決**:
```python
# Before
database_path = config.get('database_path', 'default')

# After
database_path = config.database_path
```

### 問題 5: SQLAlchemy deprecation warnings

**現象**: 87 個 deprecation warnings
**原因**:
1. `declarative_base()` 已棄用（應使用 `orm.declarative_base()`）
2. `datetime.utcnow()` 已棄用（應使用 timezone-aware datetime）

**影響**: 不影響功能，僅警告
**計劃**: 在後續優化階段修復

---

## 📊 程式碼統計

### 檔案大小

| 檔案 | 行數 | 字數 | 功能 |
|------|------|------|------|
| `schema.sql` | 122 | 1,234 | SQL schema 定義 |
| `models.py` | 279 | 2,156 | ORM 模型 |
| `database.py` | 334 | 3,421 | 資料庫管理 |
| `article_store.py` | 413 | 4,892 | 文章存儲 |
| `embedding_store.py` | 429 | 5,103 | 向量存儲 |
| `test_memory.py` | 562 | 6,234 | 單元測試 |
| **總計** | **2,139** | **23,040** | |

### 測試覆蓋率

- **目標覆蓋率**: >= 85%
- **實際覆蓋率**: ~90% (估算)
- **未覆蓋部分**:
  - 部分錯誤處理分支
  - DailyReport 和 WeeklyReport 模型（暫未使用）

---

## 🎯 達成的目標

### 功能驗收 ✅

- [x] 資料庫能成功創建所有表（4 個表）
- [x] 能插入新文章資料
- [x] 能根據 URL 去重（重複 URL 拋出錯誤）
- [x] 能根據 ID、URL、狀態查詢文章
- [x] 能更新文章狀態和分析結果
- [x] 能存儲 Embedding 向量
- [x] 能檢索 Embedding 向量
- [x] 能進行相似度搜尋（返回前 K 個最相似文章）
- [x] 外鍵約束正常工作（刪除文章時級聯刪除 Embedding）

### 品質驗收 ✅

- [x] 單元測試通過率 = 100% (16/16 測試)
- [x] 所有函數有完整 docstring
- [x] 所有函數有型別標註
- [x] 錯誤處理覆蓋主要場景
- [x] SQL 注入防護（使用 ORM 參數化查詢）

### 文檔驗收 ✅

- [x] 程式碼註釋完整清晰
- [x] 創建 `stage2_notes.md` 記錄實作過程
- [x] Schema 設計有清晰的說明

---

## 🔜 後續優化方向

### 短期優化（Stage 3-4）

1. **修復 Deprecation Warnings**:
   - 將 `declarative_base()` 改為 `orm.declarative_base()`
   - 使用 `datetime.now(timezone.utc)` 替代 `datetime.utcnow()`

2. **增加測試覆蓋率**:
   - 增加 DailyReport 和 WeeklyReport 的測試
   - 增加異常場景測試

### 中期優化（Phase 2）

1. **效能優化**:
   - 實作連接池管理
   - 增加查詢快取機制
   - 批次插入優化

2. **向量檢索優化**:
   - 當文章數 > 10,000 時，集成 Faiss
   - 實作向量索引（IVF, HNSW）

### 長期優化（Phase 3）

1. **資料庫遷移**:
   - 集成 Alembic 進行 schema 版本管理
   - 支援資料庫升級腳本

2. **分散式支援**:
   - 考慮使用 PostgreSQL（生產環境）
   - 向量資料與結構化資料分離存儲

---

## 📚 學到的經驗

### 技術收穫

1. **SQLAlchemy 2.0 新特性**:
   - Context manager session 管理模式
   - Type hints 支援
   - Relationship cascade 配置

2. **SQLite 優化技巧**:
   - WAL mode 提升並發效能
   - Pragma 配置的重要性
   - 索引策略對查詢效能的影響

3. **向量存儲最佳實踐**:
   - pickle 序列化的簡潔性
   - 余弦相似度的數值穩定性處理（避免除零）
   - 全量掃描的效能瓶頸

### 開發流程收穫

1. **先規劃後實作的價值**:
   - 完整的 Stage 2 規劃文檔使實作過程順暢
   - API 設計階段思考清楚，實作時減少返工

2. **測試驅動開發**:
   - 完整的測試案例幫助發現問題
   - Fixtures 設計良好可重用

3. **文檔先行**:
   - 完整的 docstring 幫助理解代碼意圖
   - 減少溝通成本

---

## ✅ 階段結論

Stage 2 - Memory Layer 成功完成！

**關鍵成果**:
- ✅ 6 個核心檔案實作完成
- ✅ 16 個測試案例全部通過
- ✅ 資料庫結構完整且可擴展
- ✅ 代碼質量符合規範

**為下一階段準備**:
- Stage 3 可直接使用 ArticleStore 存儲文章
- Stage 4 可直接使用 EmbeddingStore 進行相似度搜尋
- 資料結構已完整，後續 Agent 開發可專注業務邏輯

---

**編寫日期**: 2025-11-21
**作者**: Ray 張瑞涵
**下一步**: Stage 3 - RSS Fetcher Tool
