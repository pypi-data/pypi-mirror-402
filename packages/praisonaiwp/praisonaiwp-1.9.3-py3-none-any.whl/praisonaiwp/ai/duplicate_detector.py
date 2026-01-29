"""
Duplicate Content Detector for WordPress
Uses semantic similarity via embeddings to detect duplicate/similar content.
Includes persistent caching to avoid re-indexing on every search.
"""
import hashlib
import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path.home() / ".praisonaiwp" / "cache"
CACHE_DB = CACHE_DIR / "embeddings.db"


@dataclass
class DuplicateResult:
    """Result of a duplicate check."""
    is_duplicate: bool
    similarity_score: float
    post_id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    status: str = "unique"  # unique, similar, duplicate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "similarity_score": self.similarity_score,
            "post_id": self.post_id,
            "title": self.title,
            "url": self.url,
            "status": self.status
        }


@dataclass
class DuplicateCheckResponse:
    """Response from duplicate check."""
    query: str
    threshold: float
    matches: List[DuplicateResult] = field(default_factory=list)
    total_posts_checked: int = 0
    has_duplicates: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "threshold": self.threshold,
            "matches": [m.to_dict() for m in self.matches],
            "total_posts_checked": self.total_posts_checked,
            "has_duplicates": self.has_duplicates,
            "duplicate_count": sum(1 for m in self.matches if m.is_duplicate)
        }


def _get_vector_tool():
    """Lazy import SQLiteVectorTool from praisonai_tools."""
    try:
        from praisonai_tools import SQLiteVectorTool
        return SQLiteVectorTool(path=str(CACHE_DB))
    except ImportError:
        logger.warning("praisonai_tools not installed, falling back to local cache")
        return None


class EmbeddingCache:
    """
    Embedding cache using SQLiteVectorTool from praisonai_tools.
    Falls back to local SQLite implementation if not available.
    """
    
    def __init__(self, db_path: Path = CACHE_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tool = _get_vector_tool()
        if not self._tool:
            self._init_local_db()
    
    def _init_local_db(self):
        """Initialize local SQLite database (fallback)."""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    post_id INTEGER PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    content_hash TEXT,
                    embedding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON embeddings(content_hash)")
    
    def get(self, post_id: int) -> Optional[Tuple[str, List[float], Dict]]:
        """Get cached embedding for a post."""
        if self._tool:
            results = self._tool.get(collection="wp_posts", ids=[str(post_id)])
            if results and not any("error" in r for r in results):
                for r in results:
                    if r.get("id") == str(post_id):
                        meta = r.get("metadata") or {}
                        return meta.get("title", ""), [], meta
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT title, url, embedding FROM embeddings WHERE post_id = ?",
                    (post_id,)
                ).fetchone()
                if row:
                    return row[0], json.loads(row[2]), {"title": row[0], "url": row[1]}
        return None
    
    def set(self, post_id: int, title: str, url: str, content_hash: str, embedding: List[float]):
        """Cache embedding for a post."""
        if self._tool:
            self._tool.add(
                collection="wp_posts",
                documents=[f"{title}"],
                embeddings=[embedding],
                ids=[str(post_id)],
                metadatas=[{"title": title, "url": url, "content_hash": content_hash}]
            )
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings (post_id, title, url, content_hash, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (post_id, title, url, content_hash, json.dumps(embedding)))
    
    def get_all(self) -> List[Tuple[int, str, str, List[float]]]:
        """Get all cached embeddings."""
        if self._tool:
            results = self._tool.get(collection="wp_posts")
            items = []
            for r in results:
                if "error" not in r:
                    meta = r.get("metadata") or {}
                    items.append((
                        int(r["id"]),
                        meta.get("title", ""),
                        meta.get("url", ""),
                        []  # Embeddings not stored in get results
                    ))
            return items
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT post_id, title, url, embedding FROM embeddings"
                ).fetchall()
                return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]
    
    def query(self, embedding: List[float], n_results: int = 10) -> List[Dict]:
        """Query similar embeddings using vector store."""
        if self._tool:
            return self._tool.query(
                collection="wp_posts",
                query_embeddings=[embedding],
                n_results=n_results
            )
        return []
    
    def count(self) -> int:
        """Count cached embeddings."""
        if self._tool:
            result = self._tool.count(collection="wp_posts")
            return result.get("count", 0)
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    
    def clear(self):
        """Clear all cached embeddings."""
        if self._tool:
            self._tool.clear(collection="wp_posts")
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM embeddings")
        logger.info("Embedding cache cleared")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class DuplicateDetector:
    """
    Detects duplicate content in WordPress using embedding-based semantic similarity.
    
    Uses persistent SQLite cache to avoid re-indexing on every search.
    """
    
    def __init__(
        self,
        wp_client,
        threshold: float = 0.7,
        duplicate_threshold: float = 0.95,
        embedding_model: str = "text-embedding-3-small",
        use_cache: bool = True,
        verbose: int = 0
    ):
        """
        Initialize the duplicate detector.
        
        Args:
            wp_client: WordPress client instance
            threshold: Minimum similarity to flag as similar (0-1)
            duplicate_threshold: Similarity threshold to flag as duplicate (0-1)
            embedding_model: Model to use for embeddings
            use_cache: Whether to use persistent cache
            verbose: Verbosity level
        """
        self.wp_client = wp_client
        self.threshold = threshold
        self.duplicate_threshold = duplicate_threshold
        self.embedding_model = embedding_model
        self.use_cache = use_cache
        self.verbose = verbose
        
        # Persistent cache
        self.cache = EmbeddingCache() if use_cache else None
        
        # In-memory embeddings for current session
        self._embeddings: Dict[int, Tuple[str, str, List[float]]] = {}
        self._indexed = False
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using praisonai.embedding()."""
        try:
            import praisonai
            return praisonai.embedding(text, model=self.embedding_model)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    def _content_hash(self, text: str) -> str:
        """Generate hash for content."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_post_text(self, post: Dict) -> str:
        """Extract searchable text from a post."""
        title = post.get("post_title", post.get("title", ""))
        content = ""
        
        if "post_content" in post:
            content = post["post_content"]
        elif "content" in post:
            content = post["content"]
        elif "ID" in post:
            try:
                content = self.wp_client.get_post(post["ID"], field="post_content")
            except Exception as e:
                logger.warning(f"Failed to get content for post {post['ID']}: {e}")
        
        content = str(content)[:1000] if content else ""
        return f"{title}\n\n{content}"
    
    def index_posts(
        self,
        post_type: str = "post",
        post_status: str = "publish",
        category: Optional[str] = None,
        force: bool = False
    ) -> int:
        """
        Index all posts for similarity search.
        Uses persistent cache - only indexes new/changed posts.
        
        Args:
            post_type: Type of posts to index
            post_status: Status filter
            category: Category filter (optional)
            force: Force re-indexing even if cached
            
        Returns:
            Number of posts indexed (new + from cache)
        """
        # Load from cache first
        if self.cache and not force:
            cached_count = self.cache.count()
            if cached_count > 0:
                logger.info(f"Loading {cached_count} embeddings from cache...")
                for post_id, title, url, embedding in self.cache.get_all():
                    self._embeddings[post_id] = (title, url, embedding)
                self._indexed = True
                if self.verbose:
                    print(f"Loaded {cached_count} cached embeddings")
                # Still fetch posts to check for new ones
        
        logger.info(f"Fetching {post_type}s with status={post_status}...")
        
        filters = {"post_status": post_status, "posts_per_page": 500}
        if category:
            filters["category_name"] = category
        
        posts = self.wp_client.list_posts(post_type=post_type, **filters)
        
        if not posts:
            logger.warning("No posts found")
            return len(self._embeddings)
        
        # Index only new posts
        new_indexed = 0
        for post in posts:
            post_id = post.get("ID")
            if not post_id:
                continue
            
            # Skip if already in memory
            if post_id in self._embeddings:
                continue
            
            text = self._get_post_text(post)
            if not text.strip():
                continue
            
            title = post.get("post_title", "")
            url = post.get("guid", "")
            
            # Get embedding
            try:
                embedding = self._get_embedding(text)
            except Exception as e:
                logger.error(f"Failed to embed post {post_id}: {e}")
                continue
            
            # Store in memory and cache
            self._embeddings[post_id] = (title, url, embedding)
            if self.cache:
                content_hash = self._content_hash(text)
                self.cache.set(post_id, title, url, content_hash, embedding)
            
            new_indexed += 1
            if self.verbose and new_indexed % 50 == 0:
                print(f"Indexed {new_indexed} new posts...")
        
        self._indexed = True
        total = len(self._embeddings)
        logger.info(f"Indexed {new_indexed} new posts (total: {total})")
        if self.verbose:
            print(f"Indexed {new_indexed} new posts (total: {total} in cache)")
        
        return total
    
    def check_duplicate(
        self,
        content: str,
        title: Optional[str] = None,
        exclude_post_id: Optional[int] = None,
        top_k: int = 5
    ) -> DuplicateCheckResponse:
        """
        Check if content is a duplicate of existing posts.
        """
        if not self._indexed:
            self.index_posts()
        
        query = f"{title}\n\n{content}" if title else content
        query_embedding = self._get_embedding(query)
        
        # Compute similarities
        similarities = []
        for post_id, (post_title, url, embedding) in self._embeddings.items():
            if exclude_post_id and post_id == exclude_post_id:
                continue
            
            score = cosine_similarity(query_embedding, embedding)
            similarities.append((post_id, post_title, url, score))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[3], reverse=True)
        
        # Build response
        matches = []
        has_duplicates = False
        
        for post_id, post_title, url, score in similarities[:top_k]:
            if score < self.threshold:
                continue
            
            is_duplicate = score >= self.duplicate_threshold
            if is_duplicate:
                status = "duplicate"
                has_duplicates = True
            else:
                status = "similar"
            
            matches.append(DuplicateResult(
                is_duplicate=is_duplicate,
                similarity_score=score,
                post_id=post_id,
                title=post_title,
                url=url,
                status=status
            ))
        
        return DuplicateCheckResponse(
            query=query[:100] + "..." if len(query) > 100 else query,
            threshold=self.threshold,
            matches=matches,
            total_posts_checked=len(self._embeddings),
            has_duplicates=has_duplicates
        )
    
    def find_related_posts(
        self,
        post: Dict,
        count: int = 5,
        similarity_threshold: Optional[float] = None,
        exclude_same_category: bool = False
    ) -> Dict[str, Any]:
        """Find posts related to the given post."""
        threshold = similarity_threshold or self.threshold
        
        if not self._indexed:
            self.index_posts()
        
        query = self._get_post_text(post)
        post_id = post.get("ID")
        query_embedding = self._get_embedding(query)
        
        # Compute similarities
        similarities = []
        for pid, (title, url, embedding) in self._embeddings.items():
            if pid == post_id:
                continue
            
            score = cosine_similarity(query_embedding, embedding)
            if score >= threshold:
                similarities.append((pid, title, url, score))
        
        similarities.sort(key=lambda x: x[3], reverse=True)
        
        related = []
        for pid, title, url, score in similarities[:count]:
            related.append({
                "id": pid,
                "title": title,
                "url": url,
                "similarity_score": score,
                "is_duplicate": score >= self.duplicate_threshold
            })
        
        return {
            "posts": related,
            "count": len(related),
            "query_post_id": post_id,
            "threshold": threshold
        }
    
    def clear_cache(self):
        """Clear the embedding cache."""
        if self.cache:
            self.cache.clear()
        self._embeddings.clear()
        self._indexed = False
        logger.info("Cache cleared")
