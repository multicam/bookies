"""
Database models and initialization for bookmark management system.
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


class DatabaseManager:
    """Manages SQLite database operations for bookmark system."""

    def __init__(self, db_path: str = "database/bookmarks.db"):
        # Handle both absolute and relative paths
        if not Path(db_path).is_absolute():
            # For relative paths, look for webapp database first
            webapp_db = Path("../database/bookmarks.db")
            if webapp_db.exists():
                self.db_path = webapp_db.resolve()
            else:
                self.db_path = Path(db_path)
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger(__name__)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        """Initialize database tables and indexes to match Prisma schema."""
        with self.get_connection() as conn:
            # Core bookmarks table (matches Prisma schema exactly)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    domain TEXT,
                    url_hash TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    source_file TEXT,
                    status TEXT DEFAULT 'active',
                    favicon_url TEXT,
                    screenshot_url TEXT,
                    content_type TEXT,
                    language TEXT,
                    read_status BOOLEAN DEFAULT false,
                    favorite BOOLEAN DEFAULT false
                )
            """)

            # Tags table (matches Prisma schema)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#6B7280',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)

            # Many-to-many relationship between bookmarks and tags (matches Prisma schema)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookmark_tags (
                    bookmark_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (bookmark_id, tag_id),
                    FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE ON UPDATE NO ACTION,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE ON UPDATE NO ACTION
                )
            """)

            # Collections (hierarchical folders) - matches Prisma schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    color TEXT DEFAULT '#6B7280',
                    icon TEXT,
                    FOREIGN KEY (parent_id) REFERENCES collections(id) ON DELETE SET NULL ON UPDATE NO ACTION
                )
            """)

            # Many-to-many relationship between bookmarks and collections - matches Prisma schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookmark_collections (
                    bookmark_id INTEGER NOT NULL,
                    collection_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (bookmark_id, collection_id),
                    FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE ON UPDATE NO ACTION,
                    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE ON UPDATE NO ACTION
                )
            """)

            # Import history for tracking processed files - matches Prisma schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    import_type TEXT NOT NULL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    bookmarks_imported INTEGER DEFAULT 0,
                    bookmarks_skipped INTEGER DEFAULT 0,
                    errors TEXT,
                    UNIQUE(file_path, file_hash)
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_domain ON bookmarks(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_source ON bookmarks(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_url_hash ON bookmarks(url_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collections_parent_id ON collections(parent_id)")
            
            # Optimized indexes for deduplication queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_status_domain ON bookmarks(status, domain) WHERE status = 'active'")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_status_url_hash ON bookmarks(status, url_hash) WHERE status = 'active'")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_domain_created ON bookmarks(domain, created_at) WHERE status = 'active'")

            # Full-text search virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS bookmark_search USING fts5(
                    title, description, url, tags,
                    content='bookmarks', content_rowid='id'
                )
            """)

            # Trigger to keep FTS table in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS bookmark_search_insert AFTER INSERT ON bookmarks
                BEGIN
                    INSERT INTO bookmark_search(rowid, title, description, url, tags)
                    SELECT
                        NEW.id,
                        NEW.title,
                        NEW.description,
                        NEW.url,
                        COALESCE(
                            (SELECT GROUP_CONCAT(t.name, ' ')
                             FROM tags t
                             JOIN bookmark_tags bt ON t.id = bt.tag_id
                             WHERE bt.bookmark_id = NEW.id),
                            ''
                        );
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS bookmark_search_update AFTER UPDATE ON bookmarks
                BEGIN
                    UPDATE bookmark_search
                    SET title = NEW.title,
                        description = NEW.description,
                        url = NEW.url,
                        tags = COALESCE(
                            (SELECT GROUP_CONCAT(t.name, ' ')
                             FROM tags t
                             JOIN bookmark_tags bt ON t.id = bt.tag_id
                             WHERE bt.bookmark_id = NEW.id),
                            ''
                        )
                    WHERE rowid = NEW.id;
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS bookmark_search_delete AFTER DELETE ON bookmarks
                BEGIN
                    DELETE FROM bookmark_search WHERE rowid = OLD.id;
                END
            """)

            conn.commit()
            self.logger.info("Database initialized successfully")

    def generate_url_hash(self, url: str) -> str:
        """Generate a consistent hash for URL deduplication."""
        # Normalize URL for deduplication (remove trailing slashes, fragments, etc.)
        normalized_url = url.rstrip('/').split('#')[0].lower()
        return hashlib.md5(normalized_url.encode()).hexdigest()

    def insert_bookmark(self, bookmark_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new bookmark and return its ID."""
        try:
            with self.get_connection() as conn:
                # Generate URL hash for deduplication
                url_hash = self.generate_url_hash(bookmark_data['url'])

                # Extract domain from URL
                from urllib.parse import urlparse
                domain = urlparse(bookmark_data['url']).netloc

                cursor = conn.execute("""
                    INSERT OR IGNORE INTO bookmarks
                    (url, title, description, domain, url_hash, source, source_file, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bookmark_data['url'],
                    bookmark_data.get('title', ''),
                    bookmark_data.get('description', ''),
                    domain,
                    url_hash,
                    bookmark_data.get('source', 'manual'),
                    bookmark_data.get('source_file', ''),
                    bookmark_data.get('created_at', datetime.now().isoformat())
                ))

                if cursor.rowcount > 0:
                    bookmark_id = cursor.lastrowid
                    self.logger.debug(f"Inserted bookmark: {bookmark_data['url']}")
                    return bookmark_id
                else:
                    # Bookmark already exists, get its ID
                    cursor = conn.execute(
                        "SELECT id FROM bookmarks WHERE url_hash = ?",
                        (url_hash,)
                    )
                    result = cursor.fetchone()
                    if result:
                        self.logger.debug(f"Bookmark already exists: {bookmark_data['url']}")
                        return result[0]

        except Exception as e:
            self.logger.error(f"Error inserting bookmark {bookmark_data.get('url', '')}: {e}")
            return None

    def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """Get existing tag ID or create new tag."""
        try:
            with self.get_connection() as conn:
                # Try to get existing tag
                cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                result = cursor.fetchone()

                if result:
                    return result[0]

                # Create new tag
                cursor = conn.execute(
                    "INSERT INTO tags (name) VALUES (?)",
                    (tag_name,)
                )
                return cursor.lastrowid

        except Exception as e:
            self.logger.error(f"Error getting/creating tag {tag_name}: {e}")
            return None

    def add_bookmark_tags(self, bookmark_id: int, tag_names: List[str]) -> None:
        """Add tags to a bookmark."""
        try:
            with self.get_connection() as conn:
                for tag_name in tag_names:
                    if not tag_name.strip():
                        continue

                    tag_id = self.get_or_create_tag(tag_name.strip())
                    if tag_id:
                        conn.execute("""
                            INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id)
                            VALUES (?, ?)
                        """, (bookmark_id, tag_id))

                        # Update tag usage count
                        conn.execute("""
                            UPDATE tags
                            SET usage_count = usage_count + 1
                            WHERE id = ?
                        """, (tag_id,))

        except Exception as e:
            self.logger.error(f"Error adding tags to bookmark {bookmark_id}: {e}")

    def record_import(self, filename: str, file_path: str, file_hash: str,
                     import_type: str, bookmarks_imported: int,
                     bookmarks_skipped: int, errors: str = None) -> None:
        """Record import history."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO import_history
                    (filename, file_path, file_hash, import_type,
                     bookmarks_imported, bookmarks_skipped, errors)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (filename, file_path, file_hash, import_type,
                      bookmarks_imported, bookmarks_skipped, errors))

        except Exception as e:
            self.logger.error(f"Error recording import history: {e}")

    def is_file_processed(self, file_path: str, file_hash: str) -> bool:
        """Check if a file has already been processed."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id FROM import_history
                    WHERE file_path = ? AND file_hash = ?
                """, (file_path, file_hash))
                return cursor.fetchone() is not None

        except Exception as e:
            self.logger.error(f"Error checking if file is processed: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                stats = {}

                # Get bookmark counts
                cursor = conn.execute("SELECT COUNT(*) FROM bookmarks")
                stats['total_bookmarks'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM tags")
                stats['total_tags'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM collections")
                stats['total_collections'] = cursor.fetchone()[0]

                # Get source breakdown
                cursor = conn.execute("""
                    SELECT source, COUNT(*)
                    FROM bookmarks
                    GROUP BY source
                """)
                stats['by_source'] = dict(cursor.fetchall())

                return stats

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bookmarks.log'),
            logging.StreamHandler()
        ]
    )


if __name__ == "__main__":
    setup_logging()
    db = DatabaseManager()
    stats = db.get_stats()
    print("Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")