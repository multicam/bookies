"""
Deduplication engine for bookmark management.
Handles various forms of duplicate detection and merging.
"""
import re
import hashlib
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs, urlunparse
import logging
from datetime import datetime
from collections import defaultdict

from models.database import DatabaseManager


class BookmarkDeduplicator:
    """Advanced deduplication engine for bookmarks."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication comparison."""
        try:
            # Parse the URL
            parsed = urlparse(url.lower().strip())

            # Remove common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'fb_source', 'fb_ref', 'fbclid',
                'gclid', 'gclsrc',
                'ref', 'source', 'campaign',
                '_ga', '_gac', '_gid',
                'mc_cid', 'mc_eid',
                'hsCtaTracking', 'hsa_acc', 'hsa_cam', 'hsa_grp', 'hsa_ad',
                'igshid', 'feature',
                'ncid', 'cmpid', 'sr_share'
            }

            # Parse and filter query parameters
            query_params = parse_qs(parsed.query)
            filtered_params = {}

            for key, values in query_params.items():
                if key.lower() not in tracking_params:
                    filtered_params[key] = values

            # Rebuild query string
            new_query = '&'.join([
                f"{key}={'&'.join(values)}" if len(values) > 1 else f"{key}={values[0]}"
                for key, values in sorted(filtered_params.items())
            ])

            # Rebuild URL without fragment and with normalized query
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path.rstrip('/') or '/',  # Remove trailing slash except for root
                parsed.params,
                new_query,
                ''  # Remove fragment
            ))

            return normalized

        except Exception as e:
            self.logger.debug(f"Error normalizing URL {url}: {e}")
            return url.lower().strip()

    def calculate_url_similarity(self, url1: str, url2: str) -> float:
        """Calculate similarity between two URLs."""
        # Normalize URLs first
        norm_url1 = self.normalize_url(url1)
        norm_url2 = self.normalize_url(url2)

        # Exact match after normalization
        if norm_url1 == norm_url2:
            return 1.0

        # Parse URLs
        try:
            parsed1 = urlparse(norm_url1)
            parsed2 = urlparse(norm_url2)

            # Different domains are unlikely to be duplicates
            if parsed1.netloc != parsed2.netloc:
                return 0.0

            # Compare paths using string similarity
            path_similarity = difflib.SequenceMatcher(None, parsed1.path, parsed2.path).ratio()

            # Compare query parameters
            params1 = set(parse_qs(parsed1.query).keys())
            params2 = set(parse_qs(parsed2.query).keys())

            if params1 or params2:
                param_similarity = len(params1.intersection(params2)) / len(params1.union(params2))
            else:
                param_similarity = 1.0

            # Weighted average
            return (path_similarity * 0.8) + (param_similarity * 0.2)

        except Exception as e:
            # Fallback to simple string similarity
            return difflib.SequenceMatcher(None, norm_url1, norm_url2).ratio()

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        if not title1 or not title2:
            return 0.0

        # Normalize titles
        norm_title1 = re.sub(r'[^\w\s]', '', title1.lower().strip())
        norm_title2 = re.sub(r'[^\w\s]', '', title2.lower().strip())

        if norm_title1 == norm_title2:
            return 1.0

        return difflib.SequenceMatcher(None, norm_title1, norm_title2).ratio()

    def find_exact_duplicates(self) -> List[List[Dict[str, Any]]]:
        """Find bookmarks with exactly matching normalized URLs."""
        duplicates = []

        try:
            with self.db.get_connection() as conn:
                # Group bookmarks by normalized URL hash
                cursor = conn.execute("""
                    SELECT id, url, title, created_at, source, url_hash
                    FROM bookmarks
                    WHERE status = 'active'
                    ORDER BY url_hash, created_at ASC
                """)

                url_groups = defaultdict(list)
                for row in cursor.fetchall():
                    url_groups[row['url_hash']].append(dict(row))

                # Find groups with multiple bookmarks
                for url_hash, bookmarks in url_groups.items():
                    if len(bookmarks) > 1:
                        duplicates.append(bookmarks)

        except Exception as e:
            self.logger.error(f"Error finding exact duplicates: {e}")

        return duplicates

    def find_similar_duplicates(self, similarity_threshold: float = 0.9) -> List[List[Dict[str, Any]]]:
        """Find bookmarks with similar URLs or titles."""
        duplicates = []

        try:
            with self.db.get_connection() as conn:
                # Get all active bookmarks
                cursor = conn.execute("""
                    SELECT id, url, title, created_at, source, domain
                    FROM bookmarks
                    WHERE status = 'active'
                    ORDER BY domain, created_at ASC
                """)

                bookmarks = [dict(row) for row in cursor.fetchall()]

                # Group by domain for efficiency
                domain_groups = defaultdict(list)
                for bookmark in bookmarks:
                    domain_groups[bookmark['domain']].append(bookmark)

                # Check for similarities within each domain
                for domain, domain_bookmarks in domain_groups.items():
                    if len(domain_bookmarks) < 2:
                        continue

                    checked_pairs = set()

                    for i, bookmark1 in enumerate(domain_bookmarks):
                        for j, bookmark2 in enumerate(domain_bookmarks[i+1:], i+1):
                            pair = tuple(sorted([bookmark1['id'], bookmark2['id']]))
                            if pair in checked_pairs:
                                continue
                            checked_pairs.add(pair)

                            # Calculate URL similarity
                            url_similarity = self.calculate_url_similarity(
                                bookmark1['url'], bookmark2['url']
                            )

                            # Calculate title similarity
                            title_similarity = self.calculate_title_similarity(
                                bookmark1['title'], bookmark2['title']
                            )

                            # Combined similarity (weighted toward URL)
                            combined_similarity = (url_similarity * 0.8) + (title_similarity * 0.2)

                            if combined_similarity >= similarity_threshold:
                                # Check if this pair is already in a duplicate group
                                found_group = None
                                for dup_group in duplicates:
                                    if any(b['id'] == bookmark1['id'] for b in dup_group) or \
                                       any(b['id'] == bookmark2['id'] for b in dup_group):
                                        found_group = dup_group
                                        break

                                if found_group:
                                    # Add to existing group if not already there
                                    if not any(b['id'] == bookmark1['id'] for b in found_group):
                                        found_group.append(bookmark1)
                                    if not any(b['id'] == bookmark2['id'] for b in found_group):
                                        found_group.append(bookmark2)
                                else:
                                    # Create new group
                                    duplicates.append([bookmark1, bookmark2])

        except Exception as e:
            self.logger.error(f"Error finding similar duplicates: {e}")

        return duplicates

    def merge_bookmarks(self, bookmark_ids: List[int], keep_id: Optional[int] = None) -> Optional[int]:
        """Merge multiple bookmarks into one, keeping the best data."""
        try:
            with self.db.get_connection() as conn:
                # Get all bookmark data
                placeholders = ','.join(['?' for _ in bookmark_ids])
                cursor = conn.execute(f"""
                    SELECT b.*, GROUP_CONCAT(t.name, ',') as tags
                    FROM bookmarks b
                    LEFT JOIN bookmark_tags bt ON b.id = bt.bookmark_id
                    LEFT JOIN tags t ON bt.tag_id = t.id
                    WHERE b.id IN ({placeholders})
                    GROUP BY b.id
                    ORDER BY b.created_at ASC
                """, bookmark_ids)

                bookmarks = [dict(row) for row in cursor.fetchall()]
                if not bookmarks:
                    return None

                # Determine which bookmark to keep
                if keep_id and keep_id in bookmark_ids:
                    primary_bookmark = next(b for b in bookmarks if b['id'] == keep_id)
                else:
                    # Keep the one with the most complete data or oldest
                    primary_bookmark = max(bookmarks, key=lambda b: (
                        len(b.get('title', '') or ''),
                        len(b.get('description', '') or ''),
                        bool(b.get('tags')),
                        -int(b['created_at'].timestamp() if isinstance(b['created_at'], datetime) else 0)
                    ))

                # Collect all unique tags
                all_tags = set()
                for bookmark in bookmarks:
                    if bookmark.get('tags'):
                        tags = [tag.strip() for tag in bookmark['tags'].split(',') if tag.strip()]
                        all_tags.update(tags)

                # Merge descriptions
                descriptions = [b.get('description', '').strip() for b in bookmarks
                              if b.get('description', '').strip()]
                merged_description = ' | '.join(set(descriptions))

                # Update the primary bookmark with merged data
                conn.execute("""
                    UPDATE bookmarks
                    SET description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (merged_description, primary_bookmark['id']))

                # Remove old tags and add merged tags
                conn.execute("DELETE FROM bookmark_tags WHERE bookmark_id = ?",
                           (primary_bookmark['id'],))

                for tag_name in all_tags:
                    tag_id = self.db.get_or_create_tag(tag_name)
                    if tag_id:
                        conn.execute("""
                            INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id)
                            VALUES (?, ?)
                        """, (primary_bookmark['id'], tag_id))

                # Mark other bookmarks as duplicates/archived
                other_ids = [b['id'] for b in bookmarks if b['id'] != primary_bookmark['id']]
                if other_ids:
                    other_placeholders = ','.join(['?' for _ in other_ids])
                    conn.execute(f"""
                        UPDATE bookmarks
                        SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({other_placeholders})
                    """, other_ids)

                conn.commit()
                self.logger.info(f"Merged {len(bookmark_ids)} bookmarks into bookmark {primary_bookmark['id']}")
                return primary_bookmark['id']

        except Exception as e:
            self.logger.error(f"Error merging bookmarks {bookmark_ids}: {e}")
            return None

    def auto_deduplicate(self, similarity_threshold: float = 0.95,
                        interactive: bool = False) -> Dict[str, Any]:
        """Automatically deduplicate bookmarks."""
        results = {
            'exact_duplicates_found': 0,
            'similar_duplicates_found': 0,
            'bookmarks_merged': 0,
            'bookmarks_archived': 0,
            'errors': []
        }

        try:
            self.logger.info("Starting automatic deduplication...")

            # Find exact duplicates
            exact_duplicates = self.find_exact_duplicates()
            results['exact_duplicates_found'] = len(exact_duplicates)

            for duplicate_group in exact_duplicates:
                if len(duplicate_group) > 1:
                    bookmark_ids = [b['id'] for b in duplicate_group]
                    merged_id = self.merge_bookmarks(bookmark_ids)
                    if merged_id:
                        results['bookmarks_merged'] += 1
                        results['bookmarks_archived'] += len(bookmark_ids) - 1

            # Find similar duplicates
            similar_duplicates = self.find_similar_duplicates(similarity_threshold)
            results['similar_duplicates_found'] = len(similar_duplicates)

            for duplicate_group in similar_duplicates:
                if len(duplicate_group) > 1:
                    if interactive:
                        # In interactive mode, we would ask user for confirmation
                        # For now, skip similar duplicates in auto mode
                        continue
                    else:
                        bookmark_ids = [b['id'] for b in duplicate_group]
                        merged_id = self.merge_bookmarks(bookmark_ids)
                        if merged_id:
                            results['bookmarks_merged'] += 1
                            results['bookmarks_archived'] += len(bookmark_ids) - 1

        except Exception as e:
            error_msg = f"Error in auto deduplication: {e}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def generate_deduplication_report(self) -> Dict[str, Any]:
        """Generate a report of potential duplicates for manual review."""
        report = {
            'exact_duplicates': [],
            'similar_duplicates': [],
            'statistics': {}
        }

        try:
            # Find duplicates
            exact_duplicates = self.find_exact_duplicates()
            similar_duplicates = self.find_similar_duplicates(0.85)  # Lower threshold for report

            # Format exact duplicates
            for group in exact_duplicates:
                formatted_group = []
                for bookmark in group:
                    formatted_group.append({
                        'id': bookmark['id'],
                        'url': bookmark['url'],
                        'title': bookmark['title'],
                        'source': bookmark['source'],
                        'created_at': bookmark['created_at']
                    })
                report['exact_duplicates'].append(formatted_group)

            # Format similar duplicates
            for group in similar_duplicates:
                formatted_group = []
                for bookmark in group:
                    formatted_group.append({
                        'id': bookmark['id'],
                        'url': bookmark['url'],
                        'title': bookmark['title'],
                        'source': bookmark['source'],
                        'created_at': bookmark['created_at'],
                        'similarity_scores': {
                            'url': self.calculate_url_similarity(group[0]['url'], bookmark['url']),
                            'title': self.calculate_title_similarity(group[0]['title'], bookmark['title'])
                        }
                    })
                report['similar_duplicates'].append(formatted_group)

            # Statistics
            report['statistics'] = {
                'exact_duplicate_groups': len(exact_duplicates),
                'exact_duplicate_bookmarks': sum(len(group) for group in exact_duplicates),
                'similar_duplicate_groups': len(similar_duplicates),
                'similar_duplicate_bookmarks': sum(len(group) for group in similar_duplicates),
                'total_potential_duplicates': sum(len(group) for group in exact_duplicates + similar_duplicates)
            }

        except Exception as e:
            self.logger.error(f"Error generating deduplication report: {e}")

        return report


def main():
    """Main function for testing the deduplication engine."""
    from models.database import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize database
    db = DatabaseManager()
    deduplicator = BookmarkDeduplicator(db)

    # Generate deduplication report
    logger.info("Generating deduplication report...")
    report = deduplicator.generate_deduplication_report()

    logger.info("Deduplication Report:")
    logger.info(f"  Exact duplicate groups: {report['statistics']['exact_duplicate_groups']}")
    logger.info(f"  Exact duplicate bookmarks: {report['statistics']['exact_duplicate_bookmarks']}")
    logger.info(f"  Similar duplicate groups: {report['statistics']['similar_duplicate_groups']}")
    logger.info(f"  Similar duplicate bookmarks: {report['statistics']['similar_duplicate_bookmarks']}")

    # Show some examples
    if report['exact_duplicates']:
        logger.info("Example exact duplicates:")
        for group in report['exact_duplicates'][:3]:
            logger.info(f"  Group of {len(group)} bookmarks:")
            for bookmark in group:
                logger.info(f"    {bookmark['id']}: {bookmark['url'][:60]}...")

    if report['similar_duplicates']:
        logger.info("Example similar duplicates:")
        for group in report['similar_duplicates'][:3]:
            logger.info(f"  Group of {len(group)} bookmarks:")
            for bookmark in group:
                logger.info(f"    {bookmark['id']}: {bookmark['url'][:60]}...")

    # Ask if user wants to run auto-deduplication
    try:
        response = input("Run automatic deduplication? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            logger.info("Running automatic deduplication...")
            results = deduplicator.auto_deduplicate(similarity_threshold=0.95)

            logger.info("Deduplication Results:")
            logger.info(f"  Bookmarks merged: {results['bookmarks_merged']}")
            logger.info(f"  Bookmarks archived: {results['bookmarks_archived']}")
            if results['errors']:
                logger.error("Errors:")
                for error in results['errors']:
                    logger.error(f"  {error}")

    except KeyboardInterrupt:
        logger.info("Deduplication cancelled by user")

    # Show updated database stats
    db_stats = db.get_stats()
    logger.info("Updated Database Statistics:")
    for key, value in db_stats.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()