import hashlib
import json
import sqlite3
import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 24 * 3600  # 24 hours
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_DB_PATH = CACHE_DIR / "cache.db"


@dataclass
class CacheEntry:
    query_hash: str
    query_text: str
    sources: List[Dict[str, Any]]
    answer: str
    related_questions: List[str]
    created_at: float
    updated_at: float


class CacheManager:
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT NOT NULL DEFAULT '',
                sources_json TEXT NOT NULL,
                answer TEXT NOT NULL,
                related_questions_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_updated_at ON cache (updated_at)
        """)
        conn.commit()
        conn.close()
        logger.info(f"[CACHE] Database initialized at {self.db_path}")

    def _compute_hash(self, query: str) -> str:
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[CacheEntry]:
        query_hash = self._compute_hash(query)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM cache WHERE query_hash = ?",
                (query_hash,)
            ).fetchone()
            if row is None:
                return None
            now = time.time()
            age = now - row["updated_at"]
            if age > CACHE_TTL_SECONDS:
                conn.execute("DELETE FROM cache WHERE query_hash = ?", (query_hash,))
                conn.commit()
                logger.info(f"[CACHE] Entry expired (age={age:.0f}s): {query_hash[:8]}...")
                return None
            entry = CacheEntry(
                query_hash=row["query_hash"],
                query_text=row["query_text"],
                sources=json.loads(row["sources_json"]),
                answer=row["answer"],
                related_questions=json.loads(row["related_questions_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            logger.info(f"[CACHE] Hit for: {query_hash[:8]}...")
            return entry
        except Exception as e:
            logger.error(f"[CACHE] Read error: {e}")
            return None
        finally:
            conn.close()

    def put(self, entry: CacheEntry):
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("""
                INSERT OR REPLACE INTO cache 
                (query_hash, query_text, sources_json, answer, related_questions_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.query_hash,
                entry.query_text,
                json.dumps(entry.sources, ensure_ascii=False),
                entry.answer,
                json.dumps(entry.related_questions, ensure_ascii=False),
                entry.created_at,
                entry.updated_at,
            ))
            conn.commit()
            logger.info(f"[CACHE] Stored entry: {entry.query_hash[:8]}...")
        except Exception as e:
            logger.error(f"[CACHE] Write error: {e}")
        finally:
            conn.close()

    def clear_expired(self) -> int:
        cutoff = time.time() - CACHE_TTL_SECONDS
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute("DELETE FROM cache WHERE updated_at < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            if deleted > 0:
                logger.info(f"[CACHE] Cleared {deleted} expired entries")
            return deleted
        except Exception as e:
            logger.error(f"[CACHE] Clear expired error: {e}")
            return 0
        finally:
            conn.close()

    def enforce_max_entries(self, max_entries: int = 500) -> int:
        conn = sqlite3.connect(str(self.db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            if count <= max_entries:
                return 0
            to_delete = count - max_entries
            conn.execute(
                "DELETE FROM cache WHERE query_hash IN "
                "(SELECT query_hash FROM cache ORDER BY updated_at ASC LIMIT ?)",
                (to_delete,)
            )
            conn.commit()
            logger.info(f"[CACHE] Pruned {to_delete} old entries (total={count}, max={max_entries})")
            return to_delete
        except Exception as e:
            logger.error(f"[CACHE] Prune error: {e}")
            return 0
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        try:
            row = conn.execute(
                "SELECT COUNT(*) as count, "
                "MIN(updated_at) as oldest, MAX(updated_at) as newest "
                "FROM cache"
            ).fetchone()
            return {
                "total_entries": row[0],
                "oldest_entry": row[1],
                "newest_entry": row[2],
                "db_size_bytes": os.path.getsize(self.db_path) if self.db_path.exists() else 0,
            }
        except Exception as e:
            logger.error(f"[CACHE] Stats error: {e}")
            return {"total_entries": 0}
        finally:
            conn.close()


def compute_sources_similarity(old_sources: List[Dict], new_sources: List[Dict]) -> float:
    if not old_sources and not new_sources:
        return 1.0
    if not old_sources or not new_sources:
        return 0.0

    old_urls = set(s.get("url", "") for s in old_sources if s.get("url"))
    new_urls = set(s.get("url", "") for s in new_sources if s.get("url"))
    if old_urls or new_urls:
        url_jaccard = len(old_urls & new_urls) / len(old_urls | new_urls) if (old_urls | new_urls) else 0.0
    else:
        url_jaccard = 0.0

    old_titles_words = set()
    new_titles_words = set()
    for s in old_sources:
        title = s.get("title", "")
        old_titles_words.update(_tokenize(title))
    for s in new_sources:
        title = s.get("title", "")
        new_titles_words.update(_tokenize(title))
    if old_titles_words or new_titles_words:
        title_sim = len(old_titles_words & new_titles_words) / len(old_titles_words | new_titles_words) if (old_titles_words | new_titles_words) else 0.0
    else:
        title_sim = 0.0

    len_ratio = min(len(old_sources), len(new_sources)) / max(len(old_sources), len(new_sources))

    similarity = 0.50 * url_jaccard + 0.30 * title_sim + 0.20 * len_ratio
    return similarity


def _tokenize(text: str) -> set:
    import re
    words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
    return set(w for w in words if len(w) > 1)
