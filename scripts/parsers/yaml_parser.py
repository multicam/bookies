"""
YAML bookmark parser for structured bookmark files.
Handles the +++.md format with YAML front matter.
"""
import re
import yaml
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from urllib.parse import urlparse
import logging
from datetime import datetime

from models.database import DatabaseManager


class YAMLBookmarkParser:
    """Parser for YAML structured bookmark files."""

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

    def parse_yaml_entries(self, content: str) -> Generator[Dict[str, Any], None, None]:
        """Parse YAML entries separated by --- delimiters."""
        # Split content by --- delimiters
        sections = re.split(r'^---\s*$', content, flags=re.MULTILINE)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            try:
                # Try to parse as YAML
                data = yaml.safe_load(section)

                # Skip if not a dictionary or empty
                if not isinstance(data, dict) or not data:
                    continue

                # Must have at least a URL
                if 'url' not in data or not data['url']:
                    continue

                yield data

            except yaml.YAMLError as e:
                self.logger.debug(f"Failed to parse YAML section: {e}")
                continue
            except Exception as e:
                self.logger.debug(f"Error processing YAML section: {e}")
                continue

    def normalize_bookmark_data(self, yaml_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert YAML data to normalized bookmark format."""
        try:
            url = yaml_data.get('url', '').strip()
            if not url:
                return None

            # Skip invalid URLs
            if url.startswith(('javascript:', 'data:', 'about:')):
                return None

            # Extract basic fields
            title = yaml_data.get('title', '')
            description = yaml_data.get('description', '')

            # Handle creation date
            created_at = yaml_data.get('created', yaml_data.get('created_at'))
            if created_at:
                if isinstance(created_at, str):
                    try:
                        # Handle ISO format dates
                        if 'T' in created_at:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            created_at = datetime.fromisoformat(created_at)
                    except ValueError:
                        try:
                            # Try parsing as timestamp
                            created_at = datetime.fromtimestamp(float(created_at))
                        except (ValueError, OSError):
                            created_at = datetime.now()
                elif isinstance(created_at, (int, float)):
                    try:
                        created_at = datetime.fromtimestamp(created_at)
                    except (ValueError, OSError):
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()

            # Extract tags
            tags = []
            if 'tags' in yaml_data:
                tags_data = yaml_data['tags']
                if isinstance(tags_data, list):
                    tags = [str(tag).strip() for tag in tags_data if tag]
                elif isinstance(tags_data, str):
                    tags = [tag.strip() for tag in tags_data.split(',') if tag.strip()]

            # Extract domain
            try:
                domain = urlparse(url).netloc.lower()
            except:
                domain = ''

            # Extract additional metadata
            source = yaml_data.get('source', 'manual')
            author = yaml_data.get('author', '')

            # If we have an author, add it as metadata to description
            if author and description:
                description = f"{description} (Author: {author})"
            elif author:
                description = f"Author: {author}"

            bookmark = {
                'url': url,
                'title': title if title else url,
                'description': description,
                'domain': domain,
                'created_at': created_at.isoformat(),
                'source': 'yaml_structured',
                'tags': tags,
                'yaml_id': yaml_data.get('id'),
                'original_data': yaml_data
            }

            return bookmark

        except Exception as e:
            self.logger.error(f"Error normalizing YAML data: {e}")
            return None

    def parse_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single YAML bookmark file."""
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
            self.logger.info(f"Parsing YAML file: {file_path}")

            # Check if file was already processed
            file_hash = self.calculate_file_hash(file_path)
            if self.db.is_file_processed(str(file_path), file_hash):
                self.logger.info(f"File {file_path.name} already processed, skipping")
                return results

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse YAML entries
            bookmarks = []
            for yaml_data in self.parse_yaml_entries(content):
                bookmark = self.normalize_bookmark_data(yaml_data)
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
                import_type='yaml_structured',
                bookmarks_imported=results['stats']['imported'],
                bookmarks_skipped=results['stats']['skipped'],
                errors='; '.join(results['errors']) if results['errors'] else None
            )

            self.logger.info(f"Completed parsing {file_path.name}: "
                           f"{results['stats']['imported']} imported, "
                           f"{results['stats']['skipped']} skipped, "
                           f"{results['stats']['errors']} errors")

        except Exception as e:
            error_msg = f"Error parsing file {file_path}: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def get_yaml_statistics(self, file_path: Path) -> Dict[str, Any]:
        """Get statistics about YAML bookmark file."""
        stats = {
            'total_entries': 0,
            'entries_with_ids': 0,
            'entries_with_tags': 0,
            'entries_with_authors': 0,
            'entries_with_dates': 0,
            'unique_domains': set(),
            'unique_tags': set(),
            'unique_authors': set(),
            'id_range': {'min': None, 'max': None}
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for yaml_data in self.parse_yaml_entries(content):
                stats['total_entries'] += 1

                # Count entries with IDs
                if 'id' in yaml_data and yaml_data['id']:
                    stats['entries_with_ids'] += 1
                    bookmark_id = yaml_data['id']

                    if isinstance(bookmark_id, (int, float)):
                        if stats['id_range']['min'] is None or bookmark_id < stats['id_range']['min']:
                            stats['id_range']['min'] = bookmark_id
                        if stats['id_range']['max'] is None or bookmark_id > stats['id_range']['max']:
                            stats['id_range']['max'] = bookmark_id

                # Count entries with tags
                if 'tags' in yaml_data and yaml_data['tags']:
                    stats['entries_with_tags'] += 1
                    tags = yaml_data['tags']
                    if isinstance(tags, list):
                        stats['unique_tags'].update(tags)
                    elif isinstance(tags, str):
                        stats['unique_tags'].update([t.strip() for t in tags.split(',')])

                # Count entries with authors
                if 'author' in yaml_data and yaml_data['author']:
                    stats['entries_with_authors'] += 1
                    stats['unique_authors'].add(yaml_data['author'])

                # Count entries with dates
                if 'created' in yaml_data or 'created_at' in yaml_data:
                    stats['entries_with_dates'] += 1

                # Track unique domains
                url = yaml_data.get('url', '')
                if url:
                    try:
                        domain = urlparse(url).netloc.lower()
                        if domain:
                            stats['unique_domains'].add(domain)
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Error analyzing YAML file {file_path}: {e}")

        # Convert sets to counts for JSON serialization
        stats['unique_domains'] = len(stats['unique_domains'])
        stats['unique_tags'] = len(stats['unique_tags'])
        stats['unique_authors'] = len(stats['unique_authors'])

        return stats

    def export_to_yaml(self, output_path: Path, bookmarks: List[Dict[str, Any]]) -> None:
        """Export bookmarks to YAML format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, bookmark in enumerate(bookmarks):
                    if i > 0:
                        f.write('\n---\n')
                    else:
                        f.write('---\n')

                    yaml_data = {
                        'id': bookmark.get('yaml_id') or bookmark.get('id'),
                        'url': bookmark['url']
                    }

                    if bookmark.get('title'):
                        yaml_data['title'] = bookmark['title']
                    if bookmark.get('description'):
                        yaml_data['description'] = bookmark['description']
                    if bookmark.get('tags'):
                        yaml_data['tags'] = bookmark['tags']
                    if bookmark.get('created_at'):
                        yaml_data['created'] = bookmark['created_at']
                    if bookmark.get('source'):
                        yaml_data['source'] = bookmark['source']

                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

            self.logger.info(f"Exported {len(bookmarks)} bookmarks to {output_path}")

        except Exception as e:
            self.logger.error(f"Error exporting to YAML: {e}")


def main():
    """Main function for testing the YAML parser."""
    from models.database import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database
    db = DatabaseManager()
    parser = YAMLBookmarkParser(db)

    # Parse the structured bookmarks file
    yaml_file = Path('data/ingest/+++.md')
    if not yaml_file.exists():
        logger.error(f"YAML file not found: {yaml_file}")
        return

    # Get statistics first
    stats = parser.get_yaml_statistics(yaml_file)
    logger.info("YAML File Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # Parse the file
    logger.info("Starting YAML bookmark parsing...")
    results = parser.parse_yaml_file(yaml_file)

    logger.info("YAML Parsing Results:")
    logger.info(f"  Total bookmarks found: {results['stats']['total_found']}")
    logger.info(f"  Bookmarks imported: {results['stats']['imported']}")
    logger.info(f"  Bookmarks skipped: {results['stats']['skipped']}")
    logger.info(f"  Errors: {results['stats']['errors']}")

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