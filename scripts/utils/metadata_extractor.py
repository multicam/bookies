"""
Metadata extraction and enrichment tools for bookmarks.
Extracts webpage metadata, validates links, and enriches bookmark data.
"""
import re
import requests
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.database import DatabaseManager


class MetadataExtractor:
    """Extract and enrich bookmark metadata."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def extract_page_metadata(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Extract metadata from a webpage."""
        metadata = {
            'url': url,
            'status_code': None,
            'title': '',
            'description': '',
            'keywords': [],
            'author': '',
            'language': '',
            'content_type': '',
            'favicon_url': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'og_type': '',
            'twitter_title': '',
            'twitter_description': '',
            'twitter_image': '',
            'canonical_url': '',
            'last_modified': None,
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'error': None
        }

        try:
            self.logger.debug(f"Extracting metadata from: {url}")
            response = requests.get(url, headers=self.session_headers, timeout=timeout, allow_redirects=True)
            metadata['status_code'] = response.status_code

            if response.status_code != 200:
                metadata['error'] = f"HTTP {response.status_code}"
                return metadata

            # Get content type
            metadata['content_type'] = response.headers.get('content-type', '')

            # Only process HTML content
            if 'text/html' not in metadata['content_type']:
                metadata['error'] = f"Non-HTML content: {metadata['content_type']}"
                return metadata

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic metadata
            metadata.update(self._extract_basic_meta(soup))
            metadata.update(self._extract_opengraph_meta(soup))
            metadata.update(self._extract_twitter_meta(soup))
            metadata.update(self._extract_additional_meta(soup, url))

            # Extract content statistics
            metadata['word_count'] = self._count_words(soup)

        except requests.exceptions.RequestException as e:
            metadata['error'] = f"Request failed: {str(e)}"
            self.logger.debug(f"Request failed for {url}: {e}")
        except Exception as e:
            metadata['error'] = f"Extraction failed: {str(e)}"
            self.logger.error(f"Metadata extraction failed for {url}: {e}")

        return metadata

    def _extract_basic_meta(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic HTML metadata."""
        meta = {}

        # Title
        title_tag = soup.find('title')
        meta['title'] = title_tag.get_text(strip=True) if title_tag else ''

        # Description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            meta['description'] = desc_tag.get('content', '').strip()

        # Keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            keywords = keywords_tag.get('content', '').strip()
            meta['keywords'] = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        # Author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            meta['author'] = author_tag.get('content', '').strip()

        # Language
        html_tag = soup.find('html')
        if html_tag:
            meta['language'] = html_tag.get('lang', '').strip()

        return meta

    def _extract_opengraph_meta(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Open Graph metadata."""
        meta = {}

        og_tags = {
            'og_title': 'og:title',
            'og_description': 'og:description',
            'og_image': 'og:image',
            'og_type': 'og:type'
        }

        for key, property_name in og_tags.items():
            tag = soup.find('meta', attrs={'property': property_name})
            if tag:
                meta[key] = tag.get('content', '').strip()

        return meta

    def _extract_twitter_meta(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Twitter Card metadata."""
        meta = {}

        twitter_tags = {
            'twitter_title': 'twitter:title',
            'twitter_description': 'twitter:description',
            'twitter_image': 'twitter:image'
        }

        for key, name in twitter_tags.items():
            tag = soup.find('meta', attrs={'name': name})
            if tag:
                meta[key] = tag.get('content', '').strip()

        return meta

    def _extract_additional_meta(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract additional metadata."""
        meta = {}

        # Canonical URL
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        if canonical_tag:
            meta['canonical_url'] = canonical_tag.get('href', '').strip()

        # Favicon
        favicon_candidates = [
            soup.find('link', attrs={'rel': 'icon'}),
            soup.find('link', attrs={'rel': 'shortcut icon'}),
            soup.find('link', attrs={'rel': 'apple-touch-icon'})
        ]

        for candidate in favicon_candidates:
            if candidate and candidate.get('href'):
                favicon_url = candidate.get('href')
                meta['favicon_url'] = urljoin(base_url, favicon_url)
                break

        # Last modified
        last_modified_tag = soup.find('meta', attrs={'name': 'last-modified'})
        if last_modified_tag:
            meta['last_modified'] = last_modified_tag.get('content', '').strip()

        return meta

    def _count_words(self, soup: BeautifulSoup) -> int:
        """Count words in the main content."""
        try:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()
            words = re.findall(r'\b\w+\b', text)
            return len(words)
        except:
            return 0

    def validate_bookmark_link(self, url: str) -> Dict[str, Any]:
        """Check if a bookmark URL is still valid."""
        result = {
            'url': url,
            'is_valid': False,
            'status_code': None,
            'final_url': url,
            'error': None,
            'checked_at': datetime.now().isoformat()
        }

        try:
            response = requests.head(url, headers=self.session_headers, timeout=10,
                                   allow_redirects=True)
            result['status_code'] = response.status_code
            result['final_url'] = response.url
            result['is_valid'] = 200 <= response.status_code < 400

        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
            # Try with GET if HEAD fails
            try:
                response = requests.get(url, headers=self.session_headers, timeout=10,
                                      allow_redirects=True, stream=True)
                result['status_code'] = response.status_code
                result['final_url'] = response.url
                result['is_valid'] = 200 <= response.status_code < 400
            except:
                pass

        except Exception as e:
            result['error'] = str(e)

        return result

    def enrich_bookmark(self, bookmark_id: int) -> Dict[str, Any]:
        """Enrich a single bookmark with metadata."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, url, title, description
                    FROM bookmarks
                    WHERE id = ? AND status = 'active'
                """, (bookmark_id,))

                bookmark = cursor.fetchone()
                if not bookmark:
                    return {'error': 'Bookmark not found'}

                bookmark = dict(bookmark)

                # Extract metadata
                metadata = self.extract_page_metadata(bookmark['url'])

                # Update bookmark with metadata
                updates = {}

                if not bookmark['title'] and metadata['title']:
                    updates['title'] = metadata['title']
                elif metadata['title'] and metadata['title'] != bookmark['title']:
                    # Store original title if different
                    updates['title'] = metadata['title']

                if not bookmark['description'] and metadata['description']:
                    updates['description'] = metadata['description']

                # Update additional fields
                if metadata.get('favicon_url'):
                    updates['favicon_url'] = metadata['favicon_url']

                if metadata.get('language'):
                    updates['language'] = metadata['language']

                if metadata.get('content_type'):
                    updates['content_type'] = metadata['content_type']

                # Update database
                if updates:
                    update_fields = ', '.join([f"{k} = ?" for k in updates.keys()])
                    update_values = list(updates.values()) + [bookmark_id]

                    conn.execute(f"""
                        UPDATE bookmarks
                        SET {update_fields}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, update_values)

                # Add tags based on metadata
                new_tags = []

                # Add language as tag
                if metadata.get('language'):
                    new_tags.append(f"lang:{metadata['language']}")

                # Add domain-based tags
                try:
                    domain = urlparse(bookmark['url']).netloc.lower()
                    if 'github.com' in domain:
                        new_tags.append('code')
                    elif any(blog in domain for blog in ['medium.com', 'dev.to', 'blog']):
                        new_tags.append('blog')
                    elif any(design in domain for design in ['dribbble', 'behance', 'figma']):
                        new_tags.append('design')
                except:
                    pass

                # Add content type tags
                if metadata.get('og_type'):
                    new_tags.append(f"type:{metadata['og_type']}")

                # Add keywords as tags
                if metadata.get('keywords'):
                    new_tags.extend(metadata['keywords'][:5])  # Limit to 5 keywords

                # Add new tags to database
                if new_tags:
                    self.db.add_bookmark_tags(bookmark_id, new_tags)

                conn.commit()

                return {
                    'bookmark_id': bookmark_id,
                    'metadata_extracted': True,
                    'fields_updated': list(updates.keys()),
                    'tags_added': new_tags,
                    'metadata': metadata
                }

        except Exception as e:
            self.logger.error(f"Error enriching bookmark {bookmark_id}: {e}")
            return {'error': str(e)}

    def bulk_enrich_bookmarks(self, batch_size: int = 50, max_workers: int = 5) -> Dict[str, Any]:
        """Enrich multiple bookmarks in parallel."""
        results = {
            'processed': 0,
            'enriched': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            with self.db.get_connection() as conn:
                # Get bookmarks that haven't been enriched recently
                cursor = conn.execute("""
                    SELECT id, url
                    FROM bookmarks
                    WHERE status = 'active'
                      AND (updated_at IS NULL OR updated_at < date('now', '-7 days'))
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (batch_size,))

                bookmarks = [dict(row) for row in cursor.fetchall()]

            if not bookmarks:
                self.logger.info("No bookmarks found for enrichment")
                return results

            self.logger.info(f"Enriching {len(bookmarks)} bookmarks with {max_workers} workers")

            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_bookmark = {
                    executor.submit(self.enrich_bookmark, bookmark['id']): bookmark
                    for bookmark in bookmarks
                }

                # Process completed tasks
                for future in as_completed(future_to_bookmark):
                    bookmark = future_to_bookmark[future]
                    results['processed'] += 1

                    try:
                        result = future.result()
                        if 'error' in result:
                            results['errors'] += 1
                            results['error_details'].append({
                                'bookmark_id': bookmark['id'],
                                'url': bookmark['url'],
                                'error': result['error']
                            })
                        else:
                            results['enriched'] += 1

                    except Exception as e:
                        results['errors'] += 1
                        results['error_details'].append({
                            'bookmark_id': bookmark['id'],
                            'url': bookmark['url'],
                            'error': str(e)
                        })

                    # Progress logging
                    if results['processed'] % 10 == 0:
                        self.logger.info(f"Processed {results['processed']}/{len(bookmarks)} bookmarks")

        except Exception as e:
            self.logger.error(f"Error in bulk enrichment: {e}")
            results['error_details'].append({'error': str(e)})

        return results

    def validate_all_bookmarks(self, batch_size: int = 100) -> Dict[str, Any]:
        """Validate all bookmark URLs."""
        results = {
            'checked': 0,
            'valid': 0,
            'invalid': 0,
            'broken_links': []
        }

        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, url
                    FROM bookmarks
                    WHERE status = 'active'
                    ORDER BY id
                    LIMIT ?
                """, (batch_size,))

                bookmarks = [dict(row) for row in cursor.fetchall()]

            for bookmark in bookmarks:
                try:
                    validation = self.validate_bookmark_link(bookmark['url'])
                    results['checked'] += 1

                    if validation['is_valid']:
                        results['valid'] += 1
                    else:
                        results['invalid'] += 1
                        results['broken_links'].append({
                            'id': bookmark['id'],
                            'url': bookmark['url'],
                            'status_code': validation['status_code'],
                            'error': validation['error']
                        })

                        # Mark as broken in database
                        with self.db.get_connection() as conn:
                            conn.execute("""
                                UPDATE bookmarks
                                SET status = 'broken', updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (bookmark['id'],))

                    # Progress logging
                    if results['checked'] % 50 == 0:
                        self.logger.info(f"Validated {results['checked']}/{len(bookmarks)} URLs")

                except Exception as e:
                    self.logger.error(f"Error validating bookmark {bookmark['id']}: {e}")

        except Exception as e:
            self.logger.error(f"Error in bulk validation: {e}")

        return results

    def extract_favicon(self, url: str) -> Optional[str]:
        """Extract favicon URL from a webpage."""
        try:
            response = requests.get(url, headers=self.session_headers, timeout=5)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for favicon links
            favicon_selectors = [
                'link[rel="icon"]',
                'link[rel="shortcut icon"]',
                'link[rel="apple-touch-icon"]'
            ]

            for selector in favicon_selectors:
                link = soup.select_one(selector)
                if link and link.get('href'):
                    return urljoin(url, link.get('href'))

            # Fallback to default favicon
            parsed_url = urlparse(url)
            return f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"

        except Exception as e:
            self.logger.debug(f"Error extracting favicon from {url}: {e}")
            return None


def main():
    """Main function for testing the metadata extractor."""
    from models.database import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database
    db = DatabaseManager()
    extractor = MetadataExtractor(db)

    # Test metadata extraction
    test_urls = [
        'https://github.com/microsoft/vscode',
        'https://www.figma.com',
        'https://example-broken-url-12345.com'
    ]

    for url in test_urls:
        logger.info(f"Testing metadata extraction for: {url}")
        metadata = extractor.extract_page_metadata(url)
        logger.info(f"  Title: {metadata['title']}")
        logger.info(f"  Description: {metadata['description'][:100]}...")
        logger.info(f"  Status: {metadata['status_code']}")
        if metadata['error']:
            logger.info(f"  Error: {metadata['error']}")

    # Test bulk enrichment
    logger.info("Starting bulk enrichment...")
    results = extractor.bulk_enrich_bookmarks(batch_size=10, max_workers=3)

    logger.info("Bulk Enrichment Results:")
    logger.info(f"  Processed: {results['processed']}")
    logger.info(f"  Enriched: {results['enriched']}")
    logger.info(f"  Errors: {results['errors']}")

    if results['error_details']:
        logger.error("Error details:")
        for error in results['error_details'][:5]:
            logger.error(f"  {error}")

    # Show database stats
    db_stats = db.get_stats()
    logger.info("Database Statistics:")
    for key, value in db_stats.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()