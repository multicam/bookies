"""
Feed processor for categorized bookmark files.
Handles the --db-feeds/ directory with topic-based markdown files.
"""
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from urllib.parse import urlparse
import logging
from datetime import datetime

from models.database import DatabaseManager


class FeedProcessor:
    """Processor for categorized feed bookmark files."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for deduplication."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def extract_category_from_filename(self, filename: str) -> str:
        """Extract category name from filename."""
        # Remove file extension and clean up the name
        category = filename.replace('.md', '').replace('.txt', '')
        category = category.replace('-', ' ').replace('_', ' ')
        category = re.sub(r'\s+', ' ', category).strip()
        return category.title()

    def parse_markdown_entries(self, content: str) -> Generator[Dict[str, Any], None, None]:
        """Parse markdown entries separated by --- delimiters."""
        # Split content by --- delimiters
        sections = re.split(r'^---\s*$', content, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            try:
                # Parse YAML front matter if present
                yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', section, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match.group(1)
                    remaining_content = yaml_match.group(2)

                    # Parse YAML content
                    import yaml
                    try:
                        yaml_data = yaml.safe_load(yaml_content)
                        if isinstance(yaml_data, dict):
                            yield yaml_data
                            continue
                    except yaml.YAMLError:
                        pass

                # Look for simple patterns in the content
                entry_data = self.extract_simple_entry(section)
                if entry_data:
                    yield entry_data

            except Exception as e:
                self.logger.debug(f"Error processing section: {e}")
                continue

    def extract_simple_entry(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract bookmark data from simple text format."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if not lines:
            return None

        entry_data = {}

        # Look for ID pattern
        id_match = re.search(r'^id:\s*(\d+)', content, re.MULTILINE | re.IGNORECASE)
        if id_match:
            entry_data['id'] = int(id_match.group(1))

        # Look for URL pattern
        url_patterns = [
            r'^url:\s*(.+)$',
            r'^https?://\S+',
            r'https?://\S+'
        ]

        for pattern in url_patterns:
            url_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if url_match:
                url = url_match.group(1) if pattern.startswith('^url:') else url_match.group(0)
                entry_data['url'] = url.strip()
                break

        # Look for created date pattern
        created_patterns = [
            r'^created:\s*(.+)$',
            r'^created_at:\s*(.+)$',
            r'created:\s*(.+)',
        ]

        for pattern in created_patterns:
            created_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if created_match:
                entry_data['created'] = created_match.group(1).strip()
                break

        # Look for tags pattern
        tags_patterns = [
            r'^tags:\s*\[(.*?)\]',
            r'^tags:\s*(.+)$',
        ]

        for pattern in tags_patterns:
            tags_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if tags_match:
                tags_str = tags_match.group(1).strip()
                if pattern.endswith(r'\]'):
                    # Parse array format
                    tags = [t.strip(' "\'') for t in tags_str.split(',') if t.strip()]
                else:
                    tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                entry_data['tags'] = tags
                break

        # Look for source pattern
        source_match = re.search(r'^source:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if source_match:
            entry_data['source'] = source_match.group(1).strip()

        # Look for author pattern
        author_match = re.search(r'^author:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if author_match:
            entry_data['author'] = author_match.group(1).strip()

        return entry_data if 'url' in entry_data or 'id' in entry_data else None

    def normalize_feed_entry(self, entry_data: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
        """Convert feed entry data to normalized bookmark format."""
        try:
            # Skip entries without URLs
            url = entry_data.get('url', '').strip()
            if not url:
                return None

            # Skip invalid URLs
            if url.startswith(('javascript:', 'data:', 'about:')):
                return None

            # Extract basic fields
            title = entry_data.get('title', '')
            description = entry_data.get('description', '')

            # Handle creation date
            created_at = entry_data.get('created', entry_data.get('created_at'))
            if created_at:
                if isinstance(created_at, str):
                    try:
                        # Handle ISO format dates
                        if 'T' in created_at:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            # Try other common formats
                            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']:
                                try:
                                    created_at = datetime.strptime(created_at, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                created_at = datetime.now()
                    except ValueError:
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()

            # Extract tags (include category as a tag)
            tags = entry_data.get('tags', [])
            if not isinstance(tags, list):
                tags = []

            # Add category as a tag
            if category and category not in tags:
                tags.append(category)

            # Extract domain
            try:
                domain = urlparse(url).netloc.lower()
            except:
                domain = ''

            # Extract additional metadata
            source = entry_data.get('source', 'feed_category')
            author = entry_data.get('author', '')

            # Build description with metadata
            desc_parts = []
            if description:
                desc_parts.append(description)
            if author:
                desc_parts.append(f"Author: {author}")

            final_description = ' | '.join(desc_parts)

            bookmark = {
                'url': url,
                'title': title if title else url,
                'description': final_description,
                'domain': domain,
                'created_at': created_at.isoformat(),
                'source': 'feed_category',
                'category': category,
                'tags': tags,
                'feed_id': entry_data.get('id'),
                'original_data': entry_data
            }

            return bookmark

        except Exception as e:
            self.logger.error(f"Error normalizing feed entry: {e}")
            return None

    def process_feed_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single feed file."""
        results = {
            'bookmarks': [],
            'errors': [],
            'stats': {
                'total_found': 0,
                'imported': 0,
                'skipped': 0,
                'errors': 0
            }
        }

        try:
            self.logger.info(f"Processing feed file: {file_path}")

            # Check if file was already processed
            file_hash = self.calculate_file_hash(file_path)
            if self.db.is_file_processed(str(file_path), file_hash):
                self.logger.info(f"File {file_path.name} already processed, skipping")
                return results

            # Extract category from filename
            category = self.extract_category_from_filename(file_path.name)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse feed entries
            bookmarks = []
            for entry_data in self.parse_markdown_entries(content):
                bookmark = self.normalize_feed_entry(entry_data, category)
                if bookmark:
                    bookmarks.append(bookmark)

            results['bookmarks'] = bookmarks
            results['stats']['total_found'] = len(bookmarks)

            # Import bookmarks to database
            for bookmark in bookmarks:
                try:
                    bookmark_data = {
                        'url': bookmark['url'],
                        'title': bookmark['title'],
                        'description': bookmark['description'],
                        'source': bookmark['source'],
                        'source_file': str(file_path),
                        'created_at': bookmark['created_at']
                    }

                    bookmark_id = self.db.insert_bookmark(bookmark_data)
                    if bookmark_id:
                        # Add tags if present
                        if bookmark.get('tags'):
                            self.db.add_bookmark_tags(bookmark_id, bookmark['tags'])
                        results['stats']['imported'] += 1
                    else:
                        results['stats']['skipped'] += 1

                except Exception as e:
                    error_msg = f"Error importing bookmark {bookmark.get('url', '')}: {e}"
                    results['errors'].append(error_msg)
                    results['stats']['errors'] += 1
                    self.logger.error(error_msg)

            # Record import in history
            self.db.record_import(
                filename=file_path.name,
                file_path=str(file_path),
                file_hash=file_hash,
                import_type='feed_category',
                bookmarks_imported=results['stats']['imported'],
                bookmarks_skipped=results['stats']['skipped'],
                errors='; '.join(results['errors']) if results['errors'] else None
            )

            self.logger.info(f"Completed processing {file_path.name}: "
                           f"{results['stats']['imported']} imported, "
                           f"{results['stats']['skipped']} skipped, "
                           f"{results['stats']['errors']} errors")

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def process_feed_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Process all feed files in a directory."""
        results = {
            'files_processed': 0,
            'categories': {},
            'total_bookmarks': 0,
            'total_imported': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'errors': []
        }

        try:
            # Find all markdown files
            md_files = list(directory_path.glob('*.md'))

            self.logger.info(f"Found {len(md_files)} feed files to process")

            for md_file in sorted(md_files):
                try:
                    file_results = self.process_feed_file(md_file)
                    category = self.extract_category_from_filename(md_file.name)

                    results['files_processed'] += 1
                    results['categories'][category] = {
                        'file': md_file.name,
                        'bookmarks_found': file_results['stats']['total_found'],
                        'bookmarks_imported': file_results['stats']['imported']
                    }

                    results['total_bookmarks'] += file_results['stats']['total_found']
                    results['total_imported'] += file_results['stats']['imported']
                    results['total_skipped'] += file_results['stats']['skipped']
                    results['total_errors'] += file_results['stats']['errors']
                    results['errors'].extend(file_results['errors'])

                except Exception as e:
                    error_msg = f"Error processing file {md_file}: {e}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error scanning directory {directory_path}: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def get_category_statistics(self, directory_path: Path) -> Dict[str, Any]:
        """Get statistics about categories and their bookmark counts."""
        category_stats = {}

        try:
            md_files = list(directory_path.glob('*.md'))

            for md_file in md_files:
                try:
                    category = self.extract_category_from_filename(md_file.name)

                    with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    bookmark_count = 0
                    for entry_data in self.parse_markdown_entries(content):
                        if 'url' in entry_data and entry_data['url']:
                            bookmark_count += 1

                    category_stats[category] = {
                        'file': md_file.name,
                        'bookmark_count': bookmark_count,
                        'file_size': md_file.stat().st_size
                    }

                except Exception as e:
                    self.logger.error(f"Error analyzing {md_file}: {e}")

        except Exception as e:
            self.logger.error(f"Error getting category statistics: {e}")

        return dict(sorted(category_stats.items(),
                          key=lambda x: x[1]['bookmark_count'],
                          reverse=True))


def main():
    """Main function for testing the feed processor."""
    from models.database import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database
    db = DatabaseManager()
    processor = FeedProcessor(db)

    # Process the feed directory
    feeds_path = Path('data/ingest/--db-feeds')
    if not feeds_path.exists():
        logger.error(f"Feeds directory not found: {feeds_path}")
        return

    # Get statistics first
    stats = processor.get_category_statistics(feeds_path)
    logger.info("Category Statistics:")
    for category, info in list(stats.items())[:20]:  # Show top 20
        logger.info(f"  {category}: {info['bookmark_count']} bookmarks ({info['file']})")

    # Process all feed files
    logger.info("Starting feed processing...")
    results = processor.process_feed_directory(feeds_path)

    logger.info("Feed Processing Results:")
    logger.info(f"  Files processed: {results['files_processed']}")
    logger.info(f"  Total bookmarks found: {results['total_bookmarks']}")
    logger.info(f"  Bookmarks imported: {results['total_imported']}")
    logger.info(f"  Bookmarks skipped: {results['total_skipped']}")
    logger.info(f"  Errors: {results['total_errors']}")

    logger.info("Top categories by imported bookmarks:")
    sorted_categories = sorted(results['categories'].items(),
                             key=lambda x: x[1]['bookmarks_imported'],
                             reverse=True)
    for category, info in sorted_categories[:15]:
        logger.info(f"  {category}: {info['bookmarks_imported']} imported")

    if results['errors']:
        logger.error("Errors encountered:")
        for error in results['errors'][:10]:  # Show first 10 errors
            logger.error(f"  {error}")

    # Show database stats
    db_stats = db.get_stats()
    logger.info("Database Statistics:")
    for key, value in db_stats.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()