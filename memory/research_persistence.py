import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ResearchPersistence:
    """SQLite FTS5 persistence for scraped research data.

    Stores raw scraped content with metadata for retrieval across sessions.
    Enables reutilization: "Docker" research on Tuesday, "Podman" on Thursday
    can both query the same index.
    """

    def __init__(self, db_path: str = ".memory/research.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create FTS5 tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main FTS table for content
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_fts (
                id INTEGER PRIMARY KEY,
                tool TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT NOT NULL,
                markdown_raw TEXT,
                source_quality TEXT DEFAULT 'unknown',
                date_scraped TEXT NOT NULL,
                scrape_elapsed_seconds REAL,
                scrape_status TEXT DEFAULT 'ok',
                focus_areas TEXT,
                FOREIGN KEY(tool) REFERENCES tools(name)
            )
        """)

        # Migrate: Add markdown_raw column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE research_fts ADD COLUMN markdown_raw TEXT")
            logger.info("Added markdown_raw column to research_fts")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create FTS virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS research_content
            USING fts5(
                content,
                tool UNINDEXED,
                url UNINDEXED,
                tokenize='porter'
            )
        """)

        # Metadata table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_metadata (
                id INTEGER PRIMARY KEY,
                tool TEXT NOT NULL,
                last_scraped TEXT,
                total_urls_scraped INTEGER DEFAULT 0,
                focus TEXT,
                UNIQUE(tool, focus)
            )
        """)

        # Query statistics for adaptive research
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_stats (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                tool TEXT NOT NULL,
                results_count INTEGER,
                date_executed TEXT NOT NULL,
                scrape_attempted INTEGER DEFAULT 0,
                scrape_success INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Research persistence DB ready: {self.db_path}")

    def save_scraped_content(
        self,
        tool: str,
        url: str,
        title: str,
        content: str,
        source_quality: str = "unknown",
        scrape_elapsed_seconds: Optional[float] = None,
        scrape_status: str = "ok",
        focus_areas: Optional[list[str]] = None,
        markdown_raw: str = "",
    ) -> bool:
        """Save scraped URL and content to FTS index.

        Args:
            tool: Tool/technology name
            url: URL that was scraped
            title: Page title
            content: Raw extracted content (markdown/text)
            source_quality: 'official', 'trusted', 'medium', 'unknown'
            scrape_elapsed_seconds: How long the scrape took
            scrape_status: 'ok', 'truncated', 'partial', 'failed'
            focus_areas: List of focus categories (e.g., ['performance', 'security'])
            markdown_raw: Structured markdown from Crawl4AI (preserves headers/structure)

        Returns:
            True if saved successfully, False if duplicate URL
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            focus_str = json.dumps(focus_areas or [])

            # Save to main table
            cursor.execute("""
                INSERT OR IGNORE INTO research_fts
                (tool, url, title, content, markdown_raw, source_quality, date_scraped,
                 scrape_elapsed_seconds, scrape_status, focus_areas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool, url, title, content, markdown_raw, source_quality, now,
                scrape_elapsed_seconds, scrape_status, focus_str
            ))

            # Also index in FTS for full-text search
            cursor.execute("""
                INSERT INTO research_content (content, tool, url)
                VALUES (?, ?, ?)
            """, (content, tool, url))

            conn.commit()
            conn.close()

            logger.debug(f"Persisted: {tool} from {url} ({len(content)} chars)")
            return True

        except sqlite3.IntegrityError:
            logger.debug(f"URL already indexed: {url}")
            return False
        except Exception as e:
            logger.error(f"Failed to persist: {e}")
            return False

    def query_content(
        self,
        query_text: str,
        tool: Optional[str] = None,
        limit: int = 5,
        min_content_length: int = 100,
    ) -> list[dict]:
        """Search indexed research content using FTS.

        Args:
            query_text: Search query (e.g., "docker rootless performance")
            tool: Filter by tool (optional)
            limit: Max results to return
            min_content_length: Only return docs with enough content

        Returns:
            List of dicts with {url, title, content, relevance_score}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            where_clause = ""
            params = [query_text]

            if tool:
                where_clause = " AND rc.tool = ?"
                params.append(tool)

            cursor.execute(f"""
                SELECT rc.url, rf.title, rf.content, rf.date_scraped, rf.source_quality
                FROM research_content rc
                JOIN research_fts rf ON rc.url = rf.url
                WHERE research_content MATCH ? {where_clause}
                ORDER BY rank DESC
                LIMIT ?
            """, params + [limit])

            results = cursor.fetchall()
            conn.close()

            docs = []
            for url, title, content, date_scraped, source_quality in results:
                if len(content) >= min_content_length:
                    docs.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date_scraped': date_scraped,
                        'source_quality': source_quality,
                    })

            logger.debug(f"FTS query '{query_text}': {len(docs)} results")
            return docs

        except Exception as e:
            logger.error(f"FTS query failed: {e}")
            return []

    def get_tool_coverage(self, tool: str) -> dict:
        """Get stats on how much research exists for a tool."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_urls,
                    SUM(LENGTH(content)) as total_chars,
                    MIN(date_scraped) as first_scraped,
                    MAX(date_scraped) as last_scraped
                FROM research_fts
                WHERE tool = ?
            """, (tool,))

            row = cursor.fetchone()
            conn.close()

            if row[0] == 0:
                return {'total_urls': 0, 'total_chars': 0, 'status': 'no_data'}

            return {
                'total_urls': row[0],
                'total_chars': row[1],
                'first_scraped': row[2],
                'last_scraped': row[3],
            }

        except Exception as e:
            logger.error(f"Coverage query failed: {e}")
            return {}

    def get_markdown_for_url(self, url: str) -> str:
        """Retrieve structured markdown previously extracted by Crawl4AI for a URL."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT markdown_raw FROM research_fts WHERE url = ?", (url,))
            row = cursor.fetchone()
            conn.close()

            return row[0] if row and row[0] else ""

        except Exception as e:
            logger.debug(f"Failed to get markdown for {url}: {e}")
            return ""

    def get_all_markdown_for_tool(self, tool: str, limit: int = 5) -> list[tuple[str, str]]:
        """Retrieve all cached markdown for a tool (url, markdown) pairs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT url, markdown_raw FROM research_fts WHERE tool = ? AND markdown_raw != '' LIMIT ?",
                (tool, limit)
            )
            results = cursor.fetchall()
            conn.close()

            return [(url, md) for url, md in results if md]

        except Exception as e:
            logger.debug(f"Failed to get markdown for {tool}: {e}")
            return []

    def log_query_attempt(
        self,
        query: str,
        tool: str,
        results_count: int,
        scrape_attempted: bool = False,
        scrape_success: bool = False,
    ):
        """Log search query stats for adaptive research."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO query_stats
                (query, tool, results_count, date_executed, scrape_attempted, scrape_success)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query,
                tool,
                results_count,
                datetime.now().isoformat(),
                1 if scrape_attempted else 0,
                1 if scrape_success else 0,
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log query: {e}")

    def get_weak_queries(self, tool: str, threshold: int = 2) -> list[str]:
        """Find queries that returned few results (candidates for refresh)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT query, results_count
                FROM query_stats
                WHERE tool = ? AND results_count < ?
                GROUP BY query
                ORDER BY results_count ASC
            """, (tool, threshold))

            queries = [row[0] for row in cursor.fetchall()]
            conn.close()

            return queries

        except Exception as e:
            logger.error(f"Failed to get weak queries: {e}")
            return []

    def clear_old_data(self, days: int = 30):
        """Remove research data older than N days."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM research_fts
                WHERE datetime(date_scraped) < datetime('now', '-' || ? || ' days')
            """, (days,))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            if affected > 0:
                logger.info(f"Cleaned {affected} old research records")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
