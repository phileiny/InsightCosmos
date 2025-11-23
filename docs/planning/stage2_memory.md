# Stage 2: Memory Layer (記憶層)

> **階段編號**: Stage 2
> **階段目標**: 建立數據存儲與檢索能力
> **前置依賴**: Stage 1 (Foundation)
> **預計時間**: 1 天 (6-8 小時)
> **狀態**: Planning

---

## 🎯 階段目標

### 核心目標

建立 InsightCosmos 的記憶層（Memory Layer），包括：
1. 設計並創建 SQLite 資料庫 schema
2. 實現資料庫初始化與連接管理
3. 實現文章資料的 CRUD 操作
4. 實現 Embedding 向量存儲機制
5. 建立完整的測試覆蓋

### 為什麼需要這個階段？

Memory Layer 是 Agent 系統的核心：
- **持久化存儲** - 保存收集到的文章和分析結果
- **向量檢索** - 支援基於 Embedding 的相似度搜尋
- **去重機制** - 避免重複處理相同文章
- **歷史追蹤** - 記錄文章處理狀態和時間軸
- **知識累積** - 形成個人的 AI 情報知識庫

---

## 📥 輸入 (Input)

### 來自上一階段的產出

- Stage 1: Foundation
  - `src/utils/config.py` - 配置管理（包含 DATABASE_PATH）
  - `src/utils/logger.py` - 日誌系統
  - 專案目錄結構
  - 環境配置

### 外部依賴

- **Python 套件**:
  - `sqlite3` - Python 內建，無需安裝
  - `sqlalchemy>=2.0.0` - 已在 requirements.txt
  - `numpy` - Embedding 向量操作（需新增）

- **開發工具**:
  - SQLite 瀏覽器（可選，用於檢查資料庫）

---

## 📤 輸出 (Output)

### 代碼產出

```
src/memory/
├── __init__.py           # 模組初始化
├── schema.sql            # SQL schema 定義
├── database.py           # 資料庫連接與初始化
├── models.py             # 資料模型定義（SQLAlchemy）
├── article_store.py      # 文章 CRUD 操作
└── embedding_store.py    # Embedding 存儲與檢索
```

### 資料庫產出

```
data/
└── insights.db           # SQLite 資料庫檔案
    ├── articles          # 文章資料表
    ├── embeddings        # 向量資料表
    └── metadata          # 元數據表
```

### 測試產出

```
tests/unit/
└── test_memory.py        # Memory Layer 單元測試
```

### 文檔產出

- `docs/implementation/stage2_notes.md` - Stage 2 實作筆記
- `docs/validation/stage2_test_report.md` - Stage 2 測試報告

### 功能產出

- [x] SQLite 資料庫自動創建
- [x] 文章資料 CRUD 操作
- [x] Embedding 向量存儲
- [x] 向量相似度檢索
- [x] 資料去重機制

---

## 🏗️ 技術設計

### 架構圖

```
┌─────────────────────────────────────────────────────┐
│              Application Layer                      │
│         (Agents, Tools, Orchestrator)               │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              Memory Layer API                       │
│  ┌──────────────────┐      ┌──────────────────┐    │
│  │ ArticleStore     │      │ EmbeddingStore   │    │
│  │ - create()       │      │ - store()        │    │
│  │ - read()         │      │ - search()       │    │
│  │ - update()       │      │ - similar()      │    │
│  │ - delete()       │      └──────────────────┘    │
│  └──────────────────┘                               │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│           Database Layer (SQLAlchemy)               │
│  ┌──────────────────────────────────────────────┐  │
│  │         SQLite Database Engine               │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              SQLite File (insights.db)              │
└─────────────────────────────────────────────────────┘
```

---

## 📊 資料庫 Schema 設計

### 表 1: articles（文章資料表）

**用途**: 存儲收集到的文章原始資料和元數據

| 欄位名 | 型別 | 約束 | 說明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自動遞增 ID |
| url | TEXT | UNIQUE, NOT NULL | 文章 URL（唯一標識） |
| title | TEXT | NOT NULL | 文章標題 |
| content | TEXT | | 文章內容（可選） |
| summary | TEXT | | 文章摘要 |
| source | TEXT | NOT NULL | 來源（RSS/Search） |
| source_name | TEXT | | 來源名稱（feed 名稱等） |
| published_at | DATETIME | | 文章發布時間 |
| fetched_at | DATETIME | NOT NULL | 抓取時間 |
| status | TEXT | NOT NULL | 處理狀態（pending/analyzed/reported） |
| priority_score | REAL | | 優先級分數（Analyst Agent 產生） |
| analysis | TEXT | | 分析結果（JSON 格式） |
| tags | TEXT | | 標籤（逗號分隔） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 建立時間 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新時間 |

**索引**:
- `idx_url` - URL 索引（快速去重）
- `idx_status` - 狀態索引（查詢未處理文章）
- `idx_published_at` - 發布時間索引（時間範圍查詢）
- `idx_priority_score` - 優先級索引（排序查詢）

### 表 2: embeddings（向量資料表）

**用途**: 存儲文章的 Embedding 向量

| 欄位名 | 型別 | 約束 | 說明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自動遞增 ID |
| article_id | INTEGER | FOREIGN KEY, NOT NULL | 關聯的文章 ID |
| embedding | BLOB | NOT NULL | 向量資料（序列化後的 numpy array） |
| model | TEXT | NOT NULL | 使用的模型名稱 |
| dimension | INTEGER | NOT NULL | 向量維度 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 建立時間 |

**索引**:
- `idx_article_id` - 文章 ID 索引
- `UNIQUE(article_id, model)` - 同一文章同一模型只能有一個向量

### 表 3: daily_reports（每日報告表）

**用途**: 存儲每日生成的報告

| 欄位名 | 型別 | 約束 | 說明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自動遞增 ID |
| report_date | DATE | UNIQUE, NOT NULL | 報告日期 |
| article_count | INTEGER | NOT NULL | 包含的文章數量 |
| top_articles | TEXT | NOT NULL | 頂級文章 ID 列表（JSON） |
| content | TEXT | NOT NULL | 報告內容（Markdown） |
| sent_at | DATETIME | | 發送時間 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 建立時間 |

**索引**:
- `idx_report_date` - 報告日期索引

### 表 4: weekly_reports（每週報告表）

**用途**: 存儲每週生成的報告

| 欄位名 | 型別 | 約束 | 說明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自動遞增 ID |
| week_start | DATE | NOT NULL | 週開始日期 |
| week_end | DATE | NOT NULL | 週結束日期 |
| article_count | INTEGER | NOT NULL | 包含的文章數量 |
| top_themes | TEXT | | 主要主題（JSON） |
| content | TEXT | NOT NULL | 報告內容（Markdown） |
| sent_at | DATETIME | | 發送時間 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 建立時間 |

**索引**:
- `idx_week_dates` - 週日期範圍索引
- `UNIQUE(week_start, week_end)` - 同一週只能有一個報告

---

## 🔧 核心組件設計

### 組件 1: Database (database.py)

**職責**: 資料庫連接管理與初始化

**文件**: `src/memory/database.py`

**接口設計**:

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator
import sqlite3

from src.utils.config import Config
from src.utils.logger import Logger


class Database:
    """
    資料庫管理類

    職責:
    - 創建資料庫連接
    - 初始化資料庫 schema
    - 提供 session 管理
    - 啟用 SQLite 外鍵約束

    Usage:
        >>> db = Database.from_config(config)
        >>> db.init_db()
        >>> with db.get_session() as session:
        >>>     # 使用 session
        >>>     pass
    """

    def __init__(self, database_url: str, logger: Logger = None):
        """
        初始化資料庫連接

        Args:
            database_url: 資料庫連接 URL
            logger: Logger 實例
        """
        pass

    @classmethod
    def from_config(cls, config: Config) -> "Database":
        """
        從配置創建 Database 實例

        Args:
            config: Config 配置物件

        Returns:
            Database: 資料庫實例
        """
        pass

    def init_db(self) -> None:
        """
        初始化資料庫（創建所有表）

        執行 schema.sql 中的 SQL 語句
        """
        pass

    def get_session(self) -> Generator[Session, None, None]:
        """
        獲取資料庫 session（context manager）

        Yields:
            Session: SQLAlchemy session

        Example:
            >>> with db.get_session() as session:
            >>>     article = session.query(Article).first()
        """
        pass

    def close(self) -> None:
        """
        關閉資料庫連接
        """
        pass
```

---

### 組件 2: Models (models.py)

**職責**: 定義 SQLAlchemy ORM 模型

**文件**: `src/memory/models.py`

**接口設計**:

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """
    文章 ORM 模型
    """
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(Text, nullable=False)
    source_name = Column(Text)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False, default='pending')
    priority_score = Column(Float)
    analysis = Column(Text)  # JSON string
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    embeddings = relationship("Embedding", back_populates="article", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """轉換為字典"""
        pass


class Embedding(Base):
    """
    Embedding 向量 ORM 模型
    """
    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # numpy array 序列化
    model = Column(Text, nullable=False)
    dimension = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    article = relationship("Article", back_populates="embeddings")

    def to_dict(self) -> dict:
        """轉換為字典"""
        pass


class DailyReport(Base):
    """每日報告 ORM 模型"""
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True)
    report_date = Column(DateTime, unique=True, nullable=False)
    article_count = Column(Integer, nullable=False)
    top_articles = Column(Text, nullable=False)  # JSON
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyReport(Base):
    """每週報告 ORM 模型"""
    __tablename__ = 'weekly_reports'

    id = Column(Integer, primary_key=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    article_count = Column(Integer, nullable=False)
    top_themes = Column(Text)  # JSON
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### 組件 3: ArticleStore (article_store.py)

**職責**: 文章資料的 CRUD 操作

**文件**: `src/memory/article_store.py`

**接口設計**:

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.memory.models import Article
from src.memory.database import Database
from src.utils.logger import Logger


class ArticleStore:
    """
    文章存儲管理類

    提供文章資料的 CRUD 操作

    Usage:
        >>> store = ArticleStore(db)
        >>> article_id = store.create(url="...", title="...", ...)
        >>> article = store.get_by_id(article_id)
        >>> articles = store.get_by_status("pending")
    """

    def __init__(self, database: Database, logger: Logger = None):
        """初始化"""
        pass

    def create(
        self,
        url: str,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        source: str = "unknown",
        source_name: Optional[str] = None,
        published_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        創建新文章

        Args:
            url: 文章 URL
            title: 文章標題
            content: 文章內容
            summary: 文章摘要
            source: 來源（rss/search）
            source_name: 來源名稱
            published_at: 發布時間
            tags: 標籤列表

        Returns:
            int: 文章 ID

        Raises:
            ValueError: URL 已存在
        """
        pass

    def get_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取文章"""
        pass

    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """根據 URL 獲取文章（去重用）"""
        pass

    def get_by_status(
        self,
        status: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根據狀態獲取文章列表"""
        pass

    def get_recent(
        self,
        days: int = 7,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """獲取最近 N 天的文章"""
        pass

    def get_top_priority(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """獲取優先級最高的文章"""
        pass

    def update(
        self,
        article_id: int,
        **kwargs
    ) -> bool:
        """
        更新文章

        Args:
            article_id: 文章 ID
            **kwargs: 要更新的欄位

        Returns:
            bool: 是否成功
        """
        pass

    def update_status(
        self,
        article_id: int,
        status: str
    ) -> bool:
        """更新文章狀態"""
        pass

    def update_analysis(
        self,
        article_id: int,
        analysis: Dict[str, Any],
        priority_score: float
    ) -> bool:
        """更新分析結果"""
        pass

    def delete(self, article_id: int) -> bool:
        """刪除文章"""
        pass

    def exists(self, url: str) -> bool:
        """檢查 URL 是否已存在（去重）"""
        pass

    def count_by_status(self, status: str) -> int:
        """統計某狀態的文章數量"""
        pass
```

---

### 組件 4: EmbeddingStore (embedding_store.py)

**職責**: Embedding 向量存儲與相似度檢索

**文件**: `src/memory/embedding_store.py`

**接口設計**:

```python
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import pickle

from src.memory.models import Embedding, Article
from src.memory.database import Database
from src.utils.logger import Logger


class EmbeddingStore:
    """
    Embedding 存儲管理類

    提供向量存儲與相似度檢索功能

    Usage:
        >>> store = EmbeddingStore(db)
        >>> store.store(article_id=1, vector=np.array([...]), model="text-embedding-3")
        >>> similar = store.find_similar(vector=query_vector, top_k=5)
    """

    def __init__(self, database: Database, logger: Logger = None):
        """初始化"""
        pass

    def store(
        self,
        article_id: int,
        vector: np.ndarray,
        model: str = "default"
    ) -> int:
        """
        存儲 Embedding 向量

        Args:
            article_id: 文章 ID
            vector: Embedding 向量（numpy array）
            model: 模型名稱

        Returns:
            int: Embedding ID

        Raises:
            ValueError: article_id 不存在或向量已存在
        """
        pass

    def get(self, article_id: int, model: str = "default") -> Optional[np.ndarray]:
        """
        獲取文章的 Embedding 向量

        Args:
            article_id: 文章 ID
            model: 模型名稱

        Returns:
            Optional[np.ndarray]: 向量，如果不存在則返回 None
        """
        pass

    def find_similar(
        self,
        vector: np.ndarray,
        top_k: int = 10,
        model: str = "default",
        threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        查找最相似的文章

        Args:
            vector: 查詢向量
            top_k: 返回前 K 個結果
            model: 模型名稱
            threshold: 相似度閾值（余弦相似度）

        Returns:
            List[Tuple[int, float]]: [(article_id, similarity_score), ...]
                                     按相似度降序排列

        Note:
            使用余弦相似度計算
        """
        pass

    def delete(self, article_id: int, model: Optional[str] = None) -> bool:
        """
        刪除 Embedding

        Args:
            article_id: 文章 ID
            model: 模型名稱，None 表示刪除所有模型的向量

        Returns:
            bool: 是否成功
        """
        pass

    def exists(self, article_id: int, model: str = "default") -> bool:
        """檢查 Embedding 是否存在"""
        pass

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        計算余弦相似度

        Args:
            vec1: 向量 1
            vec2: 向量 2

        Returns:
            float: 相似度 [-1, 1]
        """
        pass

    @staticmethod
    def serialize_vector(vector: np.ndarray) -> bytes:
        """序列化向量為 bytes"""
        return pickle.dumps(vector)

    @staticmethod
    def deserialize_vector(data: bytes) -> np.ndarray:
        """反序列化向量"""
        return pickle.loads(data)
```

---

## 🧪 測試策略

### 單元測試

**測試文件**: `tests/unit/test_memory.py`

**測試案例清單**:

| 測試案例 ID | 測試內容 | 輸入 | 期望輸出 | 優先級 |
|-----------|---------|------|---------|--------|
| TC-2-01 | Database 初始化成功 | Config | Database 物件 | High |
| TC-2-02 | Database 創建所有表 | - | 4 個表存在 | High |
| TC-2-03 | ArticleStore 創建文章 | 文章資料 | article_id | High |
| TC-2-04 | ArticleStore URL 去重 | 重複 URL | ValueError | High |
| TC-2-05 | ArticleStore 查詢文章 | article_id | 文章資料 | High |
| TC-2-06 | ArticleStore 更新狀態 | article_id, status | True | Medium |
| TC-2-07 | ArticleStore 優先級排序 | limit=5 | 前 5 篇 | Medium |
| TC-2-08 | EmbeddingStore 存儲向量 | article_id, vector | embedding_id | High |
| TC-2-09 | EmbeddingStore 獲取向量 | article_id | np.ndarray | High |
| TC-2-10 | EmbeddingStore 相似度搜尋 | query_vector, top_k=3 | 3 個結果 | High |
| TC-2-11 | EmbeddingStore 余弦相似度 | vec1, vec2 | float [0,1] | Medium |
| TC-2-12 | ArticleStore 按日期查詢 | days=7 | 最近 7 天文章 | Medium |

---

## ✅ 驗收標準 (Acceptance Criteria)

### 功能驗收

- [ ] 資料庫能成功創建所有表（articles, embeddings, daily_reports, weekly_reports）
- [ ] 能插入新文章資料
- [ ] 能根據 URL 去重（重複 URL 拋出錯誤）
- [ ] 能根據 ID、URL、狀態查詢文章
- [ ] 能更新文章狀態和分析結果
- [ ] 能存儲 Embedding 向量
- [ ] 能檢索 Embedding 向量
- [ ] 能進行相似度搜尋（返回前 K 個最相似文章）
- [ ] 外鍵約束正常工作（刪除文章時級聯刪除 Embedding）

### 品質驗收

- [ ] 單元測試通過率 = 100% (至少 12 個測試案例)
- [ ] 程式碼覆蓋率 >= 85%
- [ ] 所有函數有完整 docstring
- [ ] 所有函數有型別標註
- [ ] 錯誤處理覆蓋主要場景
- [ ] SQL 注入防護（使用 ORM 參數化查詢）

### 效能驗收

- [ ] 插入單篇文章 < 50ms
- [ ] 查詢單篇文章 < 20ms
- [ ] 相似度搜尋（1000 篇文章）< 500ms
- [ ] 資料庫檔案大小合理（1000 篇文章 < 50MB）

### 文檔驗收

- [ ] 程式碼註釋完整清晰
- [ ] 創建 `stage2_notes.md` 記錄實作過程
- [ ] 創建 `stage2_test_report.md` 記錄測試結果
- [ ] Schema 設計有清晰的說明

---

## 🚧 風險與挑戰

### 已知風險

| 風險 | 影響 | 緩解方案 |
|------|------|---------|
| SQLite 並發寫入限制 | 中 - 多 Agent 同時寫入可能阻塞 | 使用連接池、WAL 模式、適當的超時設定 |
| Embedding 向量搜尋效能 | 中 - 全量掃描可能較慢 | 先實現基本功能，後續可考慮 Faiss 等專用向量庫 |
| 資料庫遷移 | 低 - Schema 變更需要遷移工具 | 現階段手動處理，Phase 2 考慮 Alembic |
| 磁碟空間 | 低 - 向量資料佔用空間較大 | 設定資料保留策略（如保留最近 3 個月） |

### 技術挑戰

1. **挑戰**: Embedding 向量序列化與反序列化
   - **解決方案**: 使用 pickle 序列化 numpy array 為 bytes 存入 BLOB

2. **挑戰**: 相似度搜尋效能（全量掃描）
   - **解決方案**:
     - Stage 2: 實現基本的全量掃描（適用於 < 10,000 篇文章）
     - 未來優化: 考慮使用 Faiss、Annoy 等專用向量搜尋庫

3. **挑戰**: 時區處理
   - **解決方案**: 統一使用 UTC 時間存儲，顯示時轉換為本地時區

---

## 📚 參考資料

### 技術文檔

- [SQLAlchemy 2.0 文檔](https://docs.sqlalchemy.org/en/20/)
- [SQLite 官方文檔](https://www.sqlite.org/docs.html)
- [NumPy 官方文檔](https://numpy.org/doc/)
- [余弦相似度計算](https://en.wikipedia.org/wiki/Cosine_similarity)

### 內部參考

- `CLAUDE.md` - 編碼規範
- `docs/planning/stage1_foundation.md` - Stage 1 規劃
- `docs/project_breakdown.md` - 整體規劃

---

## 📝 開發清單 (Checklist)

### 規劃階段 ✓

- [x] 完成本規劃文檔
- [x] Schema 設計完成
- [x] API 接口設計完成

### 實作階段

- [ ] 創建 `src/memory/__init__.py`
- [ ] 編寫 `schema.sql`
- [ ] 實作 `database.py`
- [ ] 實作 `models.py`
- [ ] 實作 `article_store.py`
- [ ] 實作 `embedding_store.py`
- [ ] 編寫單元測試 `test_memory.py`
- [ ] 本地測試通過
- [ ] 更新 `requirements.txt`（新增 numpy）
- [ ] 更新 `docs/implementation/dev_log.md`

### 驗證階段

- [ ] 單元測試全部通過
- [ ] 手動測試資料庫操作
- [ ] 驗證相似度搜尋正確性
- [ ] 效能基準測試
- [ ] 完成 `docs/validation/stage2_test_report.md`
- [ ] 完成 `docs/implementation/stage2_notes.md`

---

## 🎯 下一步行動

### 立即開始（實作階段）

1. 創建 `src/memory/` 目錄結構（5 分鐘）
2. 編寫 `schema.sql`（30 分鐘）
3. 實作 `database.py`（45 分鐘）
4. 實作 `models.py`（45 分鐘）
5. 實作 `article_store.py`（90 分鐘）
6. 實作 `embedding_store.py`（90 分鐘）
7. 編寫單元測試（120 分鐘）
8. 驗證與文檔（60 分鐘）

### 準備工作

- 確認 SQLAlchemy 已安裝（在 requirements.txt 中）
- 新增 numpy 到 requirements.txt
- 確認資料目錄存在（data/）

---

## 📊 時間分配

| 階段 | 預計時間 | 佔比 |
|------|---------|------|
| 規劃 | 1.0 小時 | 12.5% |
| 實作 | 5.5 小時 | 68.75% |
| 驗證 | 1.5 小時 | 18.75% |
| **總計** | **8.0 小時** | **100%** |

---

**創建日期**: 2025-11-20
**最後更新**: 2025-11-20
**負責人**: Ray 張瑞涵
**狀態**: Planning Complete → Ready for Implementation
