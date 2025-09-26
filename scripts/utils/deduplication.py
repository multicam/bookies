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
        self._url_cache = {}  # Cache for normalized URLs
        self._similarity_cache = {}  # Cache for similarity calculations

    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication comparison with caching."""
        if url in self._url_cache:
            return self._url_cache[url]
        
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

            self._url_cache[url] = normalized
            return normalized

        except Exception as e:
            self.logger.debug(f"Error normalizing URL {url}: {e}")
            fallback = url.lower().strip()
            self._url_cache[url] = fallback
            return fallback

    def calculate_url_similarity(self, url1: str, url2: str) -> float:
        """Calculate similarity between two URLs with caching and optimizations."""
        # Create cache key
        cache_key = (url1, url2) if url1 < url2 else (url2, url1)
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]
        
        # Normalize URLs first
        norm_url1 = self.normalize_url(url1)
        norm_url2 = self.normalize_url(url2)

        # Exact match after normalization
        if norm_url1 == norm_url2:
            self._similarity_cache[cache_key] = 1.0
            return 1.0

        # Parse URLs
        try:
            parsed1 = urlparse(norm_url1)
            parsed2 = urlparse(norm_url2)

            # Different domains are unlikely to be duplicates
            if parsed1.netloc != parsed2.netloc:
                self._similarity_cache[cache_key] = 0.0
                return 0.0

            # Fast path similarity check - compare first 50 chars
            if len(norm_url1) > 50 and len(norm_url2) > 50:
                prefix_similarity = sum(c1 == c2 for c1, c2 in zip(norm_url1[:50], norm_url2[:50])) / 50
                if prefix_similarity < 0.4:  # Very different URLs
                    self._similarity_cache[cache_key] = prefix_similarity * 0.6  # Scale down
                    return self._similarity_cache[cache_key]

            # Compare paths using optimized similarity
            path_similarity = self._fast_string_similarity(parsed1.path, parsed2.path)

            # Compare query parameters
            params1 = set(parse_qs(parsed1.query).keys())
            params2 = set(parse_qs(parsed2.query).keys())

            if params1 or params2:
                param_similarity = len(params1.intersection(params2)) / len(params1.union(params2))
            else:
                param_similarity = 1.0

            # Weighted average
            result = (path_similarity * 0.8) + (param_similarity * 0.2)
            self._similarity_cache[cache_key] = result
            return result

        except Exception as e:
            # Fallback to fast string similarity
            result = self._fast_string_similarity(norm_url1, norm_url2)
            self._similarity_cache[cache_key] = result
            return result

    def _fast_string_similarity(self, s1: str, s2: str) -> float:
        """Fast string similarity using optimized algorithm."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        if s1 == s2:
            return 1.0
            
        # Use Jaccard similarity for speed on long strings
        if len(s1) > 100 or len(s2) > 100:
            # Convert to character bigrams for better similarity
            bigrams1 = set(s1[i:i+2] for i in range(len(s1)-1))
            bigrams2 = set(s2[i:i+2] for i in range(len(s2)-1))
            
            if not bigrams1 and not bigrams2:
                return 1.0
            if not bigrams1 or not bigrams2:
                return 0.0
                
            intersection = len(bigrams1.intersection(bigrams2))
            union = len(bigrams1.union(bigrams2))
            return intersection / union if union > 0 else 0.0
        else:
            # Use difflib for shorter strings
            return difflib.SequenceMatcher(None, s1, s2).ratio()

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles with optimizations."""
        if not title1 or not title2:
            return 0.0

        # Normalize titles
        norm_title1 = re.sub(r'[^\w\s]', '', title1.lower().strip())
        norm_title2 = re.sub(r'[^\w\s]', '', title2.lower().strip())

        if norm_title1 == norm_title2:
            return 1.0
            
        # Quick word-based similarity for very different titles
        words1 = set(norm_title1.split())
        words2 = set(norm_title2.split())
        
        if words1 and words2:
            word_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
            if word_similarity < 0.2:  # Very different word sets
                return word_similarity * 0.5  # Scale down
        
        return self._fast_string_similarity(norm_title1, norm_title2)

    def find_exact_duplicates(self) -> List[List[Dict[str, Any]]]:
        """Find bookmarks with exactly matching normalized URLs using optimized database query."""
        duplicates = []

        try:
            with self.db.get_connection() as conn:
                # Use database-level grouping for better performance
                cursor = conn.execute("""
                    SELECT url_hash, COUNT(*) as count
                    FROM bookmarks 
                    WHERE status = 'active'
                    GROUP BY url_hash
                    HAVING count > 1
                    ORDER BY count DESC
                """)
                
                duplicate_hashes = [row['url_hash'] for row in cursor.fetchall()]
                
                if not duplicate_hashes:
                    return duplicates
                
                # Get full details only for duplicates
                placeholders = ','.join(['?' for _ in duplicate_hashes])
                cursor = conn.execute(f"""
                    SELECT id, url, title, created_at, source, url_hash
                    FROM bookmarks
                    WHERE status = 'active' AND url_hash IN ({placeholders})
                    ORDER BY url_hash, created_at ASC
                """, duplicate_hashes)
                
                # Group by url_hash
                current_group = []
                current_hash = None
                
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    if current_hash != row_dict['url_hash']:
                        if current_group and len(current_group) > 1:
                            duplicates.append(current_group)
                        current_group = [row_dict]
                        current_hash = row_dict['url_hash']
                    else:
                        current_group.append(row_dict)
                
                # Don't forget the last group
                if current_group and len(current_group) > 1:
                    duplicates.append(current_group)

        except Exception as e:
            self.logger.error(f"Error finding exact duplicates: {e}")

        return duplicates

    def find_similar_duplicates(self, similarity_threshold: float = 0.9, batch_size: int = 1000) -> List[List[Dict[str, Any]]]:
        """Find bookmarks with similar URLs or titles using optimized batch processing."""
        duplicates = []
        processed_pairs = set()

        try:
            with self.db.get_connection() as conn:
                # Get total count for progress tracking
                count_cursor = conn.execute("SELECT COUNT(*) as count FROM bookmarks WHERE status = 'active'")
                total_bookmarks = count_cursor.fetchone()['count']
                
                if total_bookmarks < 2:
                    return duplicates
                    
                self.logger.info(f"Processing {total_bookmarks} bookmarks in batches of {batch_size}")

                # Process bookmarks in batches by domain for efficiency
                cursor = conn.execute("""
                    SELECT domain, COUNT(*) as count
                    FROM bookmarks 
                    WHERE status = 'active'
                    GROUP BY domain
                    HAVING count > 1
                    ORDER BY count DESC
                """)
                
                domains_with_duplicates = [(row['domain'], row['count']) for row in cursor.fetchall()]
                
                for domain, domain_count in domains_with_duplicates:
                    if domain_count < 2:
                        continue
                        
                    # Skip domains with too many bookmarks (likely to be noisy)
                    if domain_count > 500:
                        self.logger.info(f"Skipping domain {domain} with {domain_count} bookmarks (too many)")
                        continue
                    
                    # Get bookmarks for this domain
                    domain_cursor = conn.execute("""
                        SELECT id, url, title, created_at, source, domain
                        FROM bookmarks
                        WHERE status = 'active' AND domain = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                    """, (domain, min(batch_size, domain_count)))
                    
                    domain_bookmarks = [dict(row) for row in domain_cursor.fetchall()]
                    
                    # Compare within domain using optimized algorithm
                    domain_duplicates = self._find_similar_in_batch(
                        domain_bookmarks, similarity_threshold, processed_pairs
                    )
                    duplicates.extend(domain_duplicates)

        except Exception as e:
            self.logger.error(f"Error finding similar duplicates: {e}")

        return duplicates
    
    def _find_similar_in_batch(self, bookmarks: List[Dict], threshold: float, processed_pairs: set) -> List[List[Dict]]:
        """Find similar bookmarks within a batch using optimized comparisons."""
        if len(bookmarks) < 2:
            return []
            
        duplicates = []
        
        # Pre-compute normalized data for fast comparison
        normalized_data = []
        for bookmark in bookmarks:
            norm_url = self.normalize_url(bookmark['url'])
            norm_title = re.sub(r'[^\w\s]', '', (bookmark['title'] or '').lower().strip())
            
            normalized_data.append({
                'bookmark': bookmark,
                'norm_url': norm_url,
                'norm_title': norm_title,
                'url_parts': urlparse(norm_url),
                'title_words': set(norm_title.split()) if norm_title else set()
            })
        
        # Compare pairs with early exit conditions
        for i in range(len(normalized_data)):
            for j in range(i + 1, len(normalized_data)):
                item1, item2 = normalized_data[i], normalized_data[j]
                
                # Skip if already processed
                pair = tuple(sorted([item1['bookmark']['id'], item2['bookmark']['id']]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                # Early exit conditions - skip expensive calculations if obvious non-match
                # 1. Check if URLs are too different in length
                url1_len, url2_len = len(item1['norm_url']), len(item2['norm_url'])
                if abs(url1_len - url2_len) / max(url1_len, url2_len) > 0.5:
                    continue
                    
                # 2. Check if paths are completely different
                if (item1['url_parts'].path and item2['url_parts'].path and 
                    not item1['url_parts'].path.startswith(item2['url_parts'].path[:10]) and
                    not item2['url_parts'].path.startswith(item1['url_parts'].path[:10])):
                    if len(item1['title_words'].intersection(item2['title_words'])) < 2:
                        continue
                
                # 3. Quick title word overlap check
                if item1['title_words'] and item2['title_words']:
                    word_overlap = len(item1['title_words'].intersection(item2['title_words']))
                    word_union = len(item1['title_words'].union(item2['title_words']))
                    if word_union > 0 and word_overlap / word_union < 0.3:
                        # Low word overlap, check if URLs are very similar to compensate
                        if not (item1['norm_url'] and item2['norm_url'] and
                                item1['norm_url'][:30] == item2['norm_url'][:30]):
                            continue
                
                # Now do expensive similarity calculations
                url_similarity = self.calculate_url_similarity(
                    item1['bookmark']['url'], item2['bookmark']['url']
                )
                
                # Early exit if URL similarity is too low
                if url_similarity < threshold * 0.6:  # 60% of threshold
                    continue
                    
                title_similarity = self.calculate_title_similarity(
                    item1['bookmark']['title'], item2['bookmark']['title']
                )
                
                # Combined similarity (weighted toward URL)
                combined_similarity = (url_similarity * 0.8) + (title_similarity * 0.2)
                
                if combined_similarity >= threshold:
                    # Find or create duplicate group
                    found_group = None
                    for dup_group in duplicates:
                        if any(b['id'] == item1['bookmark']['id'] for b in dup_group) or \
                           any(b['id'] == item2['bookmark']['id'] for b in dup_group):
                            found_group = dup_group
                            break
                    
                    if found_group:
                        # Add to existing group if not already there
                        if not any(b['id'] == item1['bookmark']['id'] for b in found_group):
                            found_group.append(item1['bookmark'])
                        if not any(b['id'] == item2['bookmark']['id'] for b in found_group):
                            found_group.append(item2['bookmark'])
                    else:
                        # Create new group
                        duplicates.append([item1['bookmark'], item2['bookmark']])
        
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
                    # Keep the one with the most complete data or oldest (simpler scoring)
                    primary_bookmark = max(bookmarks, key=lambda b: (
                        len(b.get('title', '') or ''),
                        len(b.get('description', '') or ''),
                        bool(b.get('tags')),
                        -b['id']  # Use ID as timestamp proxy (newer = higher ID)
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