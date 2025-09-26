"""
HTML bookmark parser for browser export files.
Handles Netscape bookmark format used by Chrome, Firefox, Edge, etc.
"""
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from models.database import DatabaseManager


class HTMLBookmarkParser:
    """Parser for HTML bookmark export files."""

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

    def extract_folder_hierarchy(self, element, path: List[str] = None, processed_elements: set = None) -> List[Dict[str, Any]]:
        """Extract bookmarks and folder structure from HTML."""
        if path is None:
            path = []
        if processed_elements is None:
            processed_elements = set()

        bookmarks = []

        # For the main DL element, we need to find ALL DT elements recursively
        # because browser exports often have malformed HTML structure
        if not path:  # This is the root call
            # Get all DT elements within this element, regardless of nesting
            all_dt_elements = element.find_all('dt')
            
            # Process each DT element, but keep track of folder structure
            for dt in all_dt_elements:
                if id(dt) in processed_elements:
                    continue
                processed_elements.add(id(dt))
                
                # Determine the path for this element by looking at its ancestors
                current_path = self._determine_folder_path(dt, element)
                
                # Check if this is a folder (H3 element)
                h3 = dt.find('h3')
                if h3:
                    folder_name = h3.get_text(strip=True)
                    # Skip main "Bookmarks" folder as it's just a container
                    if folder_name and folder_name.lower() not in ['bookmarks', 'bookmarks bar']:
                        # For folders, we don't add them as bookmarks, but we note the path
                        continue

                # Check if this is a bookmark (A element)
                link = dt.find('a')
                if link:
                    bookmark = self.extract_bookmark_info(link, current_path)
                    if bookmark:
                        bookmarks.append(bookmark)
        else:
            # For nested calls, use the old logic
            dt_children = []
            dt_children.extend(element.find_all(['dt'], recursive=False))
            for p in element.find_all('p', recursive=False):
                dt_children.extend(p.find_all('dt', recursive=False))
            
            for child in dt_children:
                if id(child) in processed_elements:
                    continue
                processed_elements.add(id(child))
                
                # Check if this is a folder (H3 element)
                h3 = child.find('h3')
                if h3:
                    folder_name = h3.get_text(strip=True)
                    if folder_name and folder_name.lower() not in ['bookmarks', 'bookmarks bar']:
                        new_path = path + [folder_name]
                        # Find the DL element that contains this folder's bookmarks
                        dl = child.find_next_sibling('dl')
                        if dl:
                            folder_bookmarks = self.extract_folder_hierarchy(dl, new_path, processed_elements)
                            bookmarks.extend(folder_bookmarks)
                        else:
                            dl = child.find('dl')
                            if dl:
                                folder_bookmarks = self.extract_folder_hierarchy(dl, new_path, processed_elements)
                                bookmarks.extend(folder_bookmarks)

                # Check if this is a bookmark (A element)
                link = child.find('a')
                if link:
                    bookmark = self.extract_bookmark_info(link, path)
                    if bookmark:
                        bookmarks.append(bookmark)

        return bookmarks
    
    def _determine_folder_path(self, dt_element, root_element) -> List[str]:
        """Determine the folder path for a DT element by examining its ancestors."""
        path = []
        
        # Walk up the DOM tree to find folder ancestors
        current = dt_element.parent
        while current and current != root_element:
            # Look for sibling DT elements with H3 (folder) elements
            if current.name in ['dl', 'p']:
                # Check if there's a preceding DT with H3 that could be a folder
                for sibling in current.find_previous_siblings():
                    if sibling.name == 'dt':
                        h3 = sibling.find('h3')
                        if h3:
                            folder_name = h3.get_text(strip=True)
                            if folder_name and folder_name.lower() not in ['bookmarks', 'bookmarks bar']:
                                path.insert(0, folder_name)
                            break
            current = current.parent
        
        return path

    def extract_bookmark_info(self, link_element, folder_path: List[str]) -> Optional[Dict[str, Any]]:
        """Extract bookmark information from anchor element."""
        try:
            url = link_element.get('href', '').strip()
            if not url or url.startswith('javascript:') or url.startswith('data:'):
                return None

            title = link_element.get_text(strip=True)
            if not title:
                title = url

            # Extract creation date
            add_date = link_element.get('add_date')
            created_at = None
            if add_date:
                try:
                    # Browser timestamps are in seconds since epoch
                    created_at = datetime.fromtimestamp(int(add_date))
                except (ValueError, OSError):
                    pass

            if not created_at:
                created_at = datetime.now()

            # Extract favicon data
            icon_data = link_element.get('icon', '')
            favicon_url = None
            if icon_data and icon_data.startswith('data:image'):
                # Store the data URL directly for now
                favicon_url = icon_data

            # Extract domain
            try:
                domain = urlparse(url).netloc.lower()
            except:
                domain = ''

            bookmark = {
                'url': url,
                'title': title,
                'description': '',  # HTML bookmarks don't typically have descriptions
                'domain': domain,
                'created_at': created_at.isoformat(),
                'favicon_url': favicon_url,
                'folder_path': folder_path,
                'tags': folder_path,  # Use folder structure as initial tags
            }

            return bookmark

        except Exception as e:
            self.logger.error(f"Error extracting bookmark info: {e}")
            return None

    def parse_html_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single HTML bookmark file."""
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
            self.logger.info(f"Parsing HTML file: {file_path}")

            # Check if file was already processed
            file_hash = self.calculate_file_hash(file_path)
            if self.db.is_file_processed(str(file_path), file_hash):
                self.logger.info(f"File {file_path.name} already processed, skipping")
                return results

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Find the main bookmark structure (usually starts with DL)
            main_dl = soup.find('dl')
            if not main_dl:
                self.logger.warning(f"No bookmark structure found in {file_path}")
                return results

            # Extract all bookmarks
            bookmarks = self.extract_folder_hierarchy(main_dl)
            results['bookmarks'] = bookmarks
            results['stats']['total_found'] = len(bookmarks)

            # Import bookmarks to database
            for bookmark in bookmarks:
                try:
                    bookmark_data = {
                        'url': bookmark['url'],
                        'title': bookmark['title'],
                        'description': bookmark.get('description', ''),
                        'source': 'browser_export',
                        'source_file': str(file_path),
                        'created_at': bookmark['created_at']
                    }

                    bookmark_id = self.db.insert_bookmark(bookmark_data)
                    if bookmark_id:
                        # Add tags based on folder structure
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
                import_type='browser_html',
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

    def parse_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Parse all HTML bookmark files in a directory."""
        results = {
            'files_processed': 0,
            'total_bookmarks': 0,
            'total_imported': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'errors': []
        }

        try:
            # Find all HTML files that look like bookmark exports
            html_files = []
            for pattern in ['bookmarks_*.html', 'Raindrop*.html', '*.html']:
                html_files.extend(directory_path.glob(pattern))

            self.logger.info(f"Found {len(html_files)} HTML files to process")

            for html_file in html_files:
                try:
                    file_results = self.parse_html_file(html_file)

                    results['files_processed'] += 1
                    results['total_bookmarks'] += file_results['stats']['total_found']
                    results['total_imported'] += file_results['stats']['imported']
                    results['total_skipped'] += file_results['stats']['skipped']
                    results['total_errors'] += file_results['stats']['errors']
                    results['errors'].extend(file_results['errors'])

                except Exception as e:
                    error_msg = f"Error processing file {html_file}: {e}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error scanning directory {directory_path}: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def get_folder_statistics(self, directory_path: Path) -> Dict[str, Any]:
        """Get statistics about bookmark folders across all HTML files."""
        folder_stats = {}

        try:
            html_files = list(directory_path.glob('bookmarks_*.html'))
            html_files.extend(directory_path.glob('Raindrop*.html'))

            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    soup = BeautifulSoup(content, 'html.parser')
                    main_dl = soup.find('dl')
                    if main_dl:
                        bookmarks = self.extract_folder_hierarchy(main_dl)

                        for bookmark in bookmarks:
                            for folder in bookmark.get('folder_path', []):
                                if folder not in folder_stats:
                                    folder_stats[folder] = 0
                                folder_stats[folder] += 1

                except Exception as e:
                    self.logger.error(f"Error analyzing {html_file}: {e}")

        except Exception as e:
            self.logger.error(f"Error getting folder statistics: {e}")

        return dict(sorted(folder_stats.items(), key=lambda x: x[1], reverse=True))


def main():
    """Main function for testing the HTML parser."""
    from models.database import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database
    db = DatabaseManager()
    parser = HTMLBookmarkParser(db)

    # Parse the ingest directory
    ingest_path = Path('data/ingest')
    if not ingest_path.exists():
        logger.error(f"Ingest directory not found: {ingest_path}")
        return

    logger.info("Starting HTML bookmark parsing...")
    results = parser.parse_directory(ingest_path)

    logger.info("HTML Parsing Results:")
    logger.info(f"  Files processed: {results['files_processed']}")
    logger.info(f"  Total bookmarks found: {results['total_bookmarks']}")
    logger.info(f"  Bookmarks imported: {results['total_imported']}")
    logger.info(f"  Bookmarks skipped: {results['total_skipped']}")
    logger.info(f"  Errors: {results['total_errors']}")

    if results['errors']:
        logger.error("Errors encountered:")
        for error in results['errors'][:10]:  # Show first 10 errors
            logger.error(f"  {error}")

    # Show folder statistics
    folder_stats = parser.get_folder_statistics(ingest_path)
    logger.info("Top bookmark folders:")
    for folder, count in list(folder_stats.items())[:10]:
        logger.info(f"  {folder}: {count} bookmarks")

    # Show database stats
    db_stats = db.get_stats()
    logger.info("Database Statistics:")
    for key, value in db_stats.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()