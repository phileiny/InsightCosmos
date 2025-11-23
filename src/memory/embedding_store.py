"""
InsightCosmos Embedding Store

Provides vector storage and similarity search functionality.

Classes:
    EmbeddingStore: Embedding vector management and similarity search

Usage:
    from src.memory.database import Database
    from src.memory.embedding_store import EmbeddingStore
    import numpy as np

    db = Database.from_config(config)
    store = EmbeddingStore(db)

    # Store embedding
    vector = np.array([0.1, 0.2, 0.3, ...])
    embedding_id = store.store(article_id=1, vector=vector, model="text-embedding-3")

    # Find similar articles
    query_vector = np.array([0.15, 0.25, 0.35, ...])
    similar = store.find_similar(vector=query_vector, top_k=5)
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import pickle
import logging

from src.memory.models import Embedding, Article
from src.memory.database import Database
from src.utils.logger import Logger


class EmbeddingStore:
    """
    Embedding vector storage and similarity search

    Provides functionality for:
    - Storing embedding vectors
    - Retrieving embeddings
    - Cosine similarity search
    - Vector serialization/deserialization

    Attributes:
        database (Database): Database instance
        logger (Logger): Logger instance

    Example:
        >>> store = EmbeddingStore(db)
        >>> vector = np.random.rand(768)
        >>> embedding_id = store.store(article_id=1, vector=vector)
        >>> similar = store.find_similar(vector=query_vector, top_k=5)
    """

    def __init__(self, database: Database, logger: Optional[logging.Logger] = None):
        """
        Initialize EmbeddingStore

        Args:
            database: Database instance
            logger: Logger instance (optional)
        """
        self.database = database
        self.logger = logger or Logger.get_logger("EmbeddingStore")

    def store(
        self,
        article_id: int,
        vector: np.ndarray,
        model: str = "default"
    ) -> int:
        """
        Store embedding vector for an article

        Args:
            article_id: Article ID
            vector: Embedding vector (numpy array)
            model: Model name (default: "default")

        Returns:
            int: Embedding ID

        Raises:
            ValueError: If article_id doesn't exist or embedding already exists

        Example:
            >>> vector = np.array([0.1, 0.2, 0.3])
            >>> embedding_id = store.store(article_id=1, vector=vector, model="text-embedding-3")
        """
        # Validate vector
        if not isinstance(vector, np.ndarray):
            raise ValueError(f"Vector must be a numpy array, got {type(vector)}")

        if vector.ndim != 1:
            raise ValueError(f"Vector must be 1-dimensional, got shape {vector.shape}")

        try:
            with self.database.get_session() as session:
                # Check if article exists
                article = session.query(Article).filter(Article.id == article_id).first()
                if not article:
                    raise ValueError(f"Article not found: {article_id}")

                # Check if embedding already exists for this article and model
                existing = session.query(Embedding).filter(
                    Embedding.article_id == article_id,
                    Embedding.model == model
                ).first()

                if existing:
                    raise ValueError(
                        f"Embedding already exists for article {article_id} with model '{model}'"
                    )

                # Serialize vector
                vector_bytes = self.serialize_vector(vector)

                # Create embedding
                embedding = Embedding(
                    article_id=article_id,
                    embedding=vector_bytes,
                    model=model,
                    dimension=len(vector)
                )

                session.add(embedding)
                session.flush()

                embedding_id = embedding.id

                self.logger.info(
                    f"Stored embedding {embedding_id} for article {article_id} "
                    f"(model: {model}, dim: {len(vector)})"
                )

                return embedding_id

        except Exception as e:
            self.logger.error(f"Failed to store embedding: {e}")
            raise

    def get(self, article_id: int, model: str = "default") -> Optional[np.ndarray]:
        """
        Get embedding vector for an article

        Args:
            article_id: Article ID
            model: Model name (default: "default")

        Returns:
            Optional[np.ndarray]: Embedding vector or None if not found

        Example:
            >>> vector = store.get(article_id=1, model="text-embedding-3")
            >>> if vector is not None:
            ...     print(f"Vector dimension: {len(vector)}")
        """
        try:
            with self.database.get_session() as session:
                embedding = session.query(Embedding).filter(
                    Embedding.article_id == article_id,
                    Embedding.model == model
                ).first()

                if not embedding:
                    return None

                # Deserialize vector
                vector = self.deserialize_vector(embedding.embedding)

                return vector

        except Exception as e:
            self.logger.error(f"Failed to get embedding: {e}")
            raise

    def find_similar(
        self,
        vector: np.ndarray,
        top_k: int = 10,
        model: str = "default",
        threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        Find most similar articles using cosine similarity

        Args:
            vector: Query vector (numpy array)
            top_k: Number of top results to return (default: 10)
            model: Model name to search within (default: "default")
            threshold: Minimum similarity threshold (default: 0.0)

        Returns:
            List[Tuple[int, float]]: List of (article_id, similarity_score) tuples
                                     ordered by similarity (descending)

        Example:
            >>> query_vector = np.array([0.1, 0.2, 0.3])
            >>> similar = store.find_similar(vector=query_vector, top_k=5, threshold=0.5)
            >>> for article_id, score in similar:
            ...     print(f"Article {article_id}: {score:.3f}")

        Note:
            This implementation uses full scan. For large datasets (>10,000 vectors),
            consider using specialized vector databases like Faiss or Annoy.
        """
        # Validate vector
        if not isinstance(vector, np.ndarray):
            raise ValueError(f"Vector must be a numpy array, got {type(vector)}")

        if vector.ndim != 1:
            raise ValueError(f"Vector must be 1-dimensional, got shape {vector.shape}")

        try:
            with self.database.get_session() as session:
                # Get all embeddings for the specified model
                embeddings = session.query(Embedding).filter(
                    Embedding.model == model
                ).all()

                if not embeddings:
                    self.logger.warning(f"No embeddings found for model '{model}'")
                    return []

                # Calculate similarities
                similarities = []

                for embedding in embeddings:
                    stored_vector = self.deserialize_vector(embedding.embedding)

                    # Check dimension match
                    if len(stored_vector) != len(vector):
                        self.logger.warning(
                            f"Dimension mismatch for embedding {embedding.id}: "
                            f"expected {len(vector)}, got {len(stored_vector)}"
                        )
                        continue

                    # Calculate cosine similarity
                    similarity = self.cosine_similarity(vector, stored_vector)

                    # Apply threshold
                    if similarity >= threshold:
                        similarities.append((embedding.article_id, float(similarity)))

                # Sort by similarity (descending) and take top K
                similarities.sort(key=lambda x: x[1], reverse=True)
                results = similarities[:top_k]

                self.logger.info(
                    f"Found {len(results)} similar articles (searched {len(embeddings)} embeddings)"
                )

                return results

        except Exception as e:
            self.logger.error(f"Failed to find similar articles: {e}")
            raise

    def delete(self, article_id: int, model: Optional[str] = None) -> bool:
        """
        Delete embedding(s) for an article

        Args:
            article_id: Article ID
            model: Model name (if None, delete all embeddings for the article)

        Returns:
            bool: True if deleted successfully, False if not found

        Example:
            >>> store.delete(article_id=1, model="text-embedding-3")  # Delete specific
            >>> store.delete(article_id=1)  # Delete all embeddings for article
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Embedding).filter(
                    Embedding.article_id == article_id
                )

                if model:
                    query = query.filter(Embedding.model == model)

                count = query.delete()

                if count == 0:
                    self.logger.warning(
                        f"No embeddings found for deletion: article_id={article_id}, model={model}"
                    )
                    return False

                self.logger.info(
                    f"Deleted {count} embedding(s) for article {article_id}"
                )

                return True

        except Exception as e:
            self.logger.error(f"Failed to delete embedding: {e}")
            raise

    def exists(self, article_id: int, model: str = "default") -> bool:
        """
        Check if embedding exists for an article

        Args:
            article_id: Article ID
            model: Model name (default: "default")

        Returns:
            bool: True if embedding exists

        Example:
            >>> if not store.exists(article_id=1, model="text-embedding-3"):
            ...     store.store(article_id=1, vector=vector, model="text-embedding-3")
        """
        try:
            with self.database.get_session() as session:
                count = session.query(Embedding).filter(
                    Embedding.article_id == article_id,
                    Embedding.model == model
                ).count()

                return count > 0

        except Exception as e:
            self.logger.error(f"Failed to check embedding existence: {e}")
            raise

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            float: Cosine similarity score in range [-1, 1]
                  1 = identical direction
                  0 = orthogonal
                  -1 = opposite direction

        Example:
            >>> vec1 = np.array([1, 0, 0])
            >>> vec2 = np.array([1, 0, 0])
            >>> similarity = EmbeddingStore.cosine_similarity(vec1, vec2)
            >>> print(similarity)  # 1.0

        Note:
            Formula: cos(θ) = (A · B) / (||A|| * ||B||)
        """
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        similarity = dot_product / (norm1 * norm2)

        return float(similarity)

    @staticmethod
    def serialize_vector(vector: np.ndarray) -> bytes:
        """
        Serialize numpy array to bytes using pickle

        Args:
            vector: Numpy array to serialize

        Returns:
            bytes: Serialized vector

        Example:
            >>> vector = np.array([0.1, 0.2, 0.3])
            >>> vector_bytes = EmbeddingStore.serialize_vector(vector)
        """
        return pickle.dumps(vector)

    @staticmethod
    def deserialize_vector(data: bytes) -> np.ndarray:
        """
        Deserialize bytes to numpy array using pickle

        Args:
            data: Serialized vector bytes

        Returns:
            np.ndarray: Deserialized numpy array

        Example:
            >>> vector = EmbeddingStore.deserialize_vector(vector_bytes)
        """
        return pickle.loads(data)

    def get_all_embeddings(
        self,
        model: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all embeddings (without vector data)

        Args:
            model: Filter by model name (optional)
            limit: Maximum number of results (optional)

        Returns:
            List[dict]: List of embedding metadata

        Example:
            >>> embeddings = store.get_all_embeddings(model="text-embedding-3", limit=100)
            >>> for emb in embeddings:
            ...     print(f"Article {emb['article_id']}: dim={emb['dimension']}")
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Embedding)

                if model:
                    query = query.filter(Embedding.model == model)

                if limit:
                    query = query.limit(limit)

                embeddings = query.all()

                return [emb.to_dict(include_vector=False) for emb in embeddings]

        except Exception as e:
            self.logger.error(f"Failed to get all embeddings: {e}")
            raise

    def count_embeddings(self, model: Optional[str] = None) -> int:
        """
        Count embeddings

        Args:
            model: Filter by model name (optional)

        Returns:
            int: Number of embeddings

        Example:
            >>> total = store.count_embeddings()
            >>> by_model = store.count_embeddings(model="text-embedding-3")
        """
        try:
            with self.database.get_session() as session:
                query = session.query(Embedding)

                if model:
                    query = query.filter(Embedding.model == model)

                count = query.count()

                return count

        except Exception as e:
            self.logger.error(f"Failed to count embeddings: {e}")
            raise
