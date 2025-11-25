"""
Vector Clustering Tool

使用 K-Means 或 DBSCAN 對文章 Embeddings 進行聚類，
識別主題集群並提取關鍵字。

Author: Ray 張瑞涵
Created: 2025-11-25
Version: 1.0.0
"""

from typing import List, Dict, Any
import numpy as np
from src.utils.logger import setup_logger


class VectorClusteringTool:
    """
    向量聚類工具

    使用 K-Means 或 DBSCAN 對文章 Embeddings 進行聚類，
    識別主題集群並提取關鍵字。

    Attributes:
        method (str): 聚類方法 ("kmeans" | "dbscan")
        n_clusters (int): 集群數量（K-Means 用）
        random_state (int): 隨機種子（確保可重現）
        logger (Logger): 日誌記錄器
    """

    def __init__(
        self,
        method: str = "kmeans",
        n_clusters: int = 4,
        random_state: int = 42
    ):
        """
        初始化聚類工具

        Args:
            method: 聚類方法，"kmeans" 或 "dbscan"
            n_clusters: 集群數量（僅 K-Means 使用）
            random_state: 隨機種子
        """
        self.method = method
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.logger = setup_logger("VectorClustering")

    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        article_metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        對 Embeddings 進行聚類

        Args:
            embeddings: 向量矩陣，shape (n_articles, embedding_dim)
            article_metadata: 文章元數據列表
                [
                    {
                        "article_id": 1,
                        "title": "...",
                        "summary": "...",
                        "tags": "AI,Robotics",
                        "priority_score": 0.85
                    },
                    ...
                ]

        Returns:
            dict: {
                "status": "success" | "error",
                "clusters": [
                    {
                        "cluster_id": 0,
                        "article_ids": [1, 5, 12, ...],
                        "article_count": 12,
                        "average_priority": 0.87,
                        "centroid": np.array([...]),  # 集群中心向量
                        "articles": [
                            {
                                "article_id": 1,
                                "title": "...",
                                "distance_to_centroid": 0.23,
                                "priority_score": 0.85
                            },
                            ...
                        ]
                    },
                    ...
                ],
                "n_clusters": 4,
                "silhouette_score": 0.65,  # 聚類質量評分
                "error_message": str,  # 錯誤時
                "suggestion": str      # 錯誤時
            }

        Example:
            >>> tool = VectorClusteringTool(n_clusters=4)
            >>> embeddings = np.random.rand(50, 768)
            >>> metadata = [{"article_id": i, "title": f"Article {i}", ...} for i in range(50)]
            >>> result = tool.cluster_embeddings(embeddings, metadata)
            >>> print(f"Found {result['n_clusters']} clusters")
        """
        try:
            # 驗證輸入
            if embeddings.shape[0] != len(article_metadata):
                return {
                    "status": "error",
                    "error_type": "dimension_mismatch",
                    "error_message": f"Embeddings count ({embeddings.shape[0]}) != metadata count ({len(article_metadata)})",
                    "suggestion": "Ensure embeddings and metadata have the same length"
                }

            if embeddings.shape[0] < 3:
                return {
                    "status": "error",
                    "error_type": "insufficient_data",
                    "error_message": f"Need at least 3 articles, got {embeddings.shape[0]}",
                    "suggestion": "Collect more articles before clustering"
                }

            # 根據方法選擇聚類算法
            if self.method == "kmeans":
                return self._cluster_kmeans(embeddings, article_metadata)
            elif self.method == "dbscan":
                return self._cluster_dbscan(embeddings, article_metadata)
            else:
                return {
                    "status": "error",
                    "error_type": "invalid_method",
                    "error_message": f"Unknown clustering method: {self.method}",
                    "suggestion": "Use 'kmeans' or 'dbscan'"
                }

        except Exception as e:
            self.logger.error(f"Clustering failed: {e}")
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "suggestion": "Check embeddings shape and article_metadata format"
            }

    def _cluster_kmeans(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        K-Means 聚類

        Args:
            embeddings: 向量矩陣
            metadata: 文章元數據

        Returns:
            dict: 聚類結果
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        # 動態調整 n_clusters（不能超過文章數量）
        n_clusters = min(self.n_clusters, len(embeddings) - 1)

        self.logger.info(f"Running K-Means clustering with k={n_clusters}...")

        # K-Means 聚類
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=10  # 多次初始化取最佳結果
        )
        labels = kmeans.fit_predict(embeddings)

        # 計算聚類質量（Silhouette Score）
        if len(set(labels)) > 1:  # 需要至少 2 個集群
            score = silhouette_score(embeddings, labels)
        else:
            score = 0.0

        self.logger.info(f"K-Means complete. Silhouette Score: {score:.3f}")

        # 組織結果
        clusters = self._organize_clusters(
            labels,
            embeddings,
            metadata,
            kmeans.cluster_centers_
        )

        return {
            "status": "success",
            "clusters": clusters,
            "n_clusters": n_clusters,
            "silhouette_score": float(score)
        }

    def _cluster_dbscan(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        DBSCAN 聚類

        Args:
            embeddings: 向量矩陣
            metadata: 文章元數據

        Returns:
            dict: 聚類結果
        """
        from sklearn.cluster import DBSCAN

        self.logger.info("Running DBSCAN clustering...")

        # DBSCAN 聚類（參數需根據實際數據調整）
        dbscan = DBSCAN(eps=0.5, min_samples=3)
        labels = dbscan.fit_predict(embeddings)

        # 計算集群數量（排除噪音點 -1）
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)
        n_clusters = len(unique_labels)

        self.logger.info(f"DBSCAN complete. Found {n_clusters} clusters")

        # 計算集群中心（手動計算平均值）
        cluster_centers = []
        for label in sorted(unique_labels):
            mask = labels == label
            centroid = embeddings[mask].mean(axis=0)
            cluster_centers.append(centroid)

        # 組織結果
        clusters = self._organize_clusters(
            labels,
            embeddings,
            metadata,
            cluster_centers if cluster_centers else None
        )

        return {
            "status": "success",
            "clusters": clusters,
            "n_clusters": n_clusters,
            "silhouette_score": None  # DBSCAN 不計算此指標
        }

    def _organize_clusters(
        self,
        labels: np.ndarray,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]],
        centroids: Any
    ) -> List[Dict[str, Any]]:
        """
        組織聚類結果

        Args:
            labels: 聚類標籤
            embeddings: 向量矩陣
            metadata: 文章元數據
            centroids: 集群中心（可以是 np.ndarray 或 list）

        Returns:
            List[dict]: 組織好的聚類結果
        """
        clusters = []
        unique_labels = set(labels)

        # 移除噪音點（DBSCAN 會產生 -1 標籤）
        if -1 in unique_labels:
            unique_labels.remove(-1)
            self.logger.warning(f"Found {sum(labels == -1)} noise points (excluded from clusters)")

        for i, label in enumerate(sorted(unique_labels)):
            mask = labels == label
            cluster_embeddings = embeddings[mask]
            cluster_metadata = [m for m, is_in in zip(metadata, mask) if is_in]

            # 計算集群中心
            if centroids is not None and i < len(centroids):
                centroid = centroids[i]
            else:
                centroid = cluster_embeddings.mean(axis=0)

            # 計算每篇文章到集群中心的距離
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)

            # 組織文章數據
            articles = []
            for meta, dist in zip(cluster_metadata, distances):
                articles.append({
                    "article_id": meta.get("article_id"),
                    "title": meta.get("title", "Untitled"),
                    "priority_score": meta.get("priority_score", 0.0),
                    "distance_to_centroid": float(dist)
                })

            # 排序（優先度高 + 距離中心近）
            articles.sort(key=lambda x: (
                -x["priority_score"],  # 優先度降序
                x["distance_to_centroid"]  # 距離升序
            ))

            # 計算平均優先度
            avg_priority = float(np.mean([a["priority_score"] for a in articles]))

            clusters.append({
                "cluster_id": int(label),
                "article_ids": [a["article_id"] for a in articles],
                "article_count": len(articles),
                "average_priority": avg_priority,
                "centroid": centroid.tolist() if isinstance(centroid, np.ndarray) else centroid,
                "articles": articles
            })

        # 按平均優先度排序集群
        clusters.sort(key=lambda x: x["average_priority"], reverse=True)

        return clusters

    def extract_cluster_keywords(
        self,
        cluster: Dict[str, Any],
        all_articles: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[str]:
        """
        提取集群關鍵字（使用 TF-IDF）

        Args:
            cluster: 單個集群數據
            all_articles: 所有文章（用於計算 IDF）
            top_k: 返回前 k 個關鍵字

        Returns:
            List[str]: 關鍵字列表

        Example:
            >>> tool = VectorClusteringTool()
            >>> keywords = tool.extract_cluster_keywords(cluster, all_articles, top_k=5)
            >>> print(keywords)
            ['multi-agent', 'robotics', 'framework', 'autonomous', 'collaboration']
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # 準備集群內文章文本
            cluster_texts = []
            for article in all_articles:
                if article.get("article_id") in cluster["article_ids"]:
                    text = article.get("title", "") + " " + article.get("summary", "")
                    cluster_texts.append(text)

            # 準備所有文章文本（背景語料）
            all_texts = [
                article.get("title", "") + " " + article.get("summary", "")
                for article in all_articles
            ]

            if not cluster_texts or not all_texts:
                return []

            # TF-IDF 向量化
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words="english",
                min_df=1,
                ngram_range=(1, 2)  # 支持 1-2 個詞的短語
            )
            vectorizer.fit(all_texts)

            # 計算集群的 TF-IDF
            cluster_tfidf = vectorizer.transform(cluster_texts)
            avg_tfidf = cluster_tfidf.mean(axis=0).A1

            # 提取 Top K 關鍵字
            top_indices = avg_tfidf.argsort()[-top_k:][::-1]
            keywords = [vectorizer.get_feature_names_out()[i] for i in top_indices]

            return keywords

        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []

    def find_representative_articles(
        self,
        cluster: Dict[str, Any],
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        找出集群代表性文章（最接近中心 + 高優先度）

        Args:
            cluster: 集群數據
            top_n: 返回前 n 篇文章

        Returns:
            List[dict]: 代表性文章列表

        Example:
            >>> tool = VectorClusteringTool()
            >>> rep_articles = tool.find_representative_articles(cluster, top_n=3)
            >>> for article in rep_articles:
            ...     print(article['title'])
        """
        # 文章已在 _organize_clusters 中排序
        return cluster["articles"][:top_n]


# ============================================================================
# 便捷函數
# ============================================================================

def cluster_articles(
    embeddings: np.ndarray,
    article_metadata: List[Dict[str, Any]],
    method: str = "kmeans",
    n_clusters: int = 4
) -> Dict[str, Any]:
    """
    便捷函數：文章聚類

    Args:
        embeddings: 向量矩陣
        article_metadata: 文章元數據列表
        method: 聚類方法 ("kmeans" 或 "dbscan")
        n_clusters: 集群數量（K-Means 用）

    Returns:
        dict: 聚類結果

    Example:
        >>> from src.tools.vector_clustering import cluster_articles
        >>> import numpy as np
        >>> embeddings = np.random.rand(50, 768)
        >>> metadata = [{"article_id": i, "title": f"Article {i}", "priority_score": 0.8} for i in range(50)]
        >>> result = cluster_articles(embeddings, metadata, n_clusters=4)
        >>> print(f"Found {result['n_clusters']} clusters")
        Found 4 clusters
    """
    tool = VectorClusteringTool(method=method, n_clusters=n_clusters)
    return tool.cluster_embeddings(embeddings, article_metadata)
