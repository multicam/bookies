"""
Command-line interface for bookmark management system.
"""
import click
from pathlib import Path
import logging
import json
from typing import List, Dict, Any, Optional

from models.database import DatabaseManager, setup_logging
from parsers.html_parser import HTMLBookmarkParser
from parsers.yaml_parser import YAMLBookmarkParser
from parsers.feed_processor import FeedProcessor
from utils.deduplication import BookmarkDeduplicator
from utils.metadata_extractor import MetadataExtractor


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--database', '-d', default='../database/bookmarks.db',
              help='Database file path (defaults to webapp database)', type=click.Path())
@click.pass_context
def cli(ctx, verbose, database):
    """Bookmark management CLI tool."""
    # Setup logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    setup_logging()

    # Initialize database
    ctx.ensure_object(dict)
    ctx.obj['db'] = DatabaseManager(database)
    ctx.obj['verbose'] = verbose

    # Log which database we're using
    click.echo(f"Using database: {ctx.obj['db'].db_path}")


@cli.command()
@click.option('--source', '-s', type=click.Choice(['all', 'html', 'yaml', 'feeds']),
              default='all', help='Import source type')
@click.option('--directory', '-d', default='data/ingest',
              help='Input directory path', type=click.Path(exists=True))
@click.pass_context
def import_bookmarks(ctx, source, directory):
    """Import bookmarks from various sources."""
    db = ctx.obj['db']
    ingest_path = Path(directory)

    click.echo(f"Importing bookmarks from: {ingest_path}")
    click.echo(f"Source types: {source}")

    total_imported = 0
    total_errors = 0

    if source in ['all', 'html']:
        click.echo("\n📄 Importing HTML bookmark files...")
        parser = HTMLBookmarkParser(db)
        results = parser.parse_directory(ingest_path)

        click.echo(f"HTML Import Results:")
        click.echo(f"  Files processed: {results['files_processed']}")
        click.echo(f"  Bookmarks imported: {results['total_imported']}")
        click.echo(f"  Bookmarks skipped: {results['total_skipped']}")
        click.echo(f"  Errors: {results['total_errors']}")

        total_imported += results['total_imported']
        total_errors += results['total_errors']

    if source in ['all', 'yaml']:
        click.echo("\n📝 Importing YAML structured bookmarks...")
        parser = YAMLBookmarkParser(db)
        yaml_file = ingest_path / '+++.md'

        if yaml_file.exists():
            results = parser.parse_yaml_file(yaml_file)

            click.echo(f"YAML Import Results:")
            click.echo(f"  Bookmarks imported: {results['stats']['imported']}")
            click.echo(f"  Bookmarks skipped: {results['stats']['skipped']}")
            click.echo(f"  Errors: {results['stats']['errors']}")

            total_imported += results['stats']['imported']
            total_errors += results['stats']['errors']
        else:
            click.echo("  No +++.md file found")

    if source in ['all', 'feeds']:
        click.echo("\n📊 Importing categorized feeds...")
        processor = FeedProcessor(db)
        feeds_path = ingest_path / '--db-feeds'

        if feeds_path.exists():
            results = processor.process_feed_directory(feeds_path)

            click.echo(f"Feed Import Results:")
            click.echo(f"  Files processed: {results['files_processed']}")
            click.echo(f"  Bookmarks imported: {results['total_imported']}")
            click.echo(f"  Bookmarks skipped: {results['total_skipped']}")
            click.echo(f"  Errors: {results['total_errors']}")

            total_imported += results['total_imported']
            total_errors += results['total_errors']
        else:
            click.echo("  No --db-feeds directory found")

    click.echo(f"\n✅ Import completed!")
    click.echo(f"Total bookmarks imported: {total_imported}")
    click.echo(f"Total errors: {total_errors}")


@cli.command()
@click.option('--similarity', '-s', default=0.9, type=float,
              help='Similarity threshold (0.0-1.0)')
@click.option('--auto', '-a', is_flag=True, help='Auto-merge without confirmation')
@click.option('--report-only', '-r', is_flag=True, help='Generate report only')
@click.pass_context
def deduplicate(ctx, similarity, auto, report_only):
    """Find and remove duplicate bookmarks."""
    db = ctx.obj['db']
    deduplicator = BookmarkDeduplicator(db)

    click.echo("🔍 Analyzing duplicates...")

    if report_only:
        report = deduplicator.generate_deduplication_report()

        click.echo("\nDeduplication Report:")
        click.echo(f"  Exact duplicate groups: {report['statistics']['exact_duplicate_groups']}")
        click.echo(f"  Similar duplicate groups: {report['statistics']['similar_duplicate_groups']}")
        click.echo(f"  Total potential duplicates: {report['statistics']['total_potential_duplicates']}")

        if report['exact_duplicates']:
            click.echo(f"\nExample exact duplicates:")
            for i, group in enumerate(report['exact_duplicates'][:3]):
                click.echo(f"  Group {i+1} ({len(group)} bookmarks):")
                for bookmark in group:
                    click.echo(f"    - {bookmark['title'][:50]}... ({bookmark['url'][:40]}...)")

        return

    if auto:
        click.echo("🤖 Running automatic deduplication...")
        results = deduplicator.auto_deduplicate(similarity_threshold=similarity)

        click.echo(f"\nDeduplication Results:")
        click.echo(f"  Bookmarks merged: {results['bookmarks_merged']}")
        click.echo(f"  Bookmarks archived: {results['bookmarks_archived']}")

        if results['errors']:
            click.echo(f"  Errors: {len(results['errors'])}")
            for error in results['errors'][:5]:
                click.echo(f"    - {error}")

    else:
        # Interactive mode
        exact_duplicates = deduplicator.find_exact_duplicates()

        if not exact_duplicates:
            click.echo("No exact duplicates found!")
            return

        click.echo(f"Found {len(exact_duplicates)} groups of exact duplicates")

        for i, group in enumerate(exact_duplicates):
            click.echo(f"\nGroup {i+1} ({len(group)} duplicates):")
            for j, bookmark in enumerate(group):
                click.echo(f"  {j+1}. {bookmark['title'][:60]}...")
                click.echo(f"     URL: {bookmark['url'][:80]}...")
                click.echo(f"     Source: {bookmark['source']} | Created: {bookmark['created_at']}")

            if click.confirm("Merge this group?"):
                bookmark_ids = [b['id'] for b in group]
                merged_id = deduplicator.merge_bookmarks(bookmark_ids)
                if merged_id:
                    click.echo(f"✅ Merged into bookmark {merged_id}")
                else:
                    click.echo("❌ Failed to merge")


@cli.command()
@click.option('--batch-size', '-b', default=50, type=int, help='Batch size for processing')
@click.option('--max-workers', '-w', default=5, type=int, help='Maximum parallel workers')
@click.pass_context
def enrich(ctx, batch_size, max_workers):
    """Enrich bookmarks with metadata from web pages."""
    db = ctx.obj['db']
    extractor = MetadataExtractor(db)

    click.echo(f"🌐 Enriching bookmarks (batch: {batch_size}, workers: {max_workers})...")

    with click.progressbar(length=batch_size, label='Enriching bookmarks') as bar:
        def update_progress():
            bar.update(1)

        results = extractor.bulk_enrich_bookmarks(batch_size, max_workers)

    click.echo(f"\nEnrichment Results:")
    click.echo(f"  Processed: {results['processed']}")
    click.echo(f"  Enriched: {results['enriched']}")
    click.echo(f"  Errors: {results['errors']}")

    if results['error_details'] and ctx.obj['verbose']:
        click.echo("\nError Details:")
        for error in results['error_details'][:10]:
            click.echo(f"  {error['url']}: {error['error']}")


@cli.command()
@click.option('--batch-size', '-b', default=100, type=int, help='Number of URLs to check')
@click.pass_context
def validate(ctx, batch_size):
    """Validate bookmark URLs and mark broken links."""
    db = ctx.obj['db']
    extractor = MetadataExtractor(db)

    click.echo(f"🔗 Validating {batch_size} bookmark URLs...")

    results = extractor.validate_all_bookmarks(batch_size)

    click.echo(f"\nValidation Results:")
    click.echo(f"  URLs checked: {results['checked']}")
    click.echo(f"  Valid URLs: {results['valid']}")
    click.echo(f"  Broken URLs: {results['invalid']}")

    if results['broken_links']:
        click.echo(f"\nBroken links found:")
        for link in results['broken_links'][:10]:
            click.echo(f"  {link['url']} (HTTP {link['status_code']})")


@cli.command()
@click.option('--query', '-q', help='Search query')
@click.option('--tag', '-t', help='Filter by tag')
@click.option('--domain', help='Filter by domain')
@click.option('--limit', '-l', default=20, type=int, help='Number of results')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'urls']),
              default='table', help='Output format')
@click.pass_context
def search(ctx, query, tag, domain, limit, format):
    """Search bookmarks."""
    db = ctx.obj['db']

    conditions = []
    params = []

    base_query = """
        SELECT b.id, b.url, b.title, b.description, b.domain, b.created_at,
               GROUP_CONCAT(t.name, ', ') as tags
        FROM bookmarks b
        LEFT JOIN bookmark_tags bt ON b.id = bt.bookmark_id
        LEFT JOIN tags t ON bt.tag_id = t.id
        WHERE b.status = 'active'
    """

    if query:
        conditions.append("b.id IN (SELECT rowid FROM bookmark_search WHERE bookmark_search MATCH ?)")
        params.append(query)

    if tag:
        conditions.append("b.id IN (SELECT bt.bookmark_id FROM bookmark_tags bt JOIN tags t ON bt.tag_id = t.id WHERE t.name LIKE ?)")
        params.append(f"%{tag}%")

    if domain:
        conditions.append("b.domain LIKE ?")
        params.append(f"%{domain}%")

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    base_query += " GROUP BY b.id ORDER BY b.created_at DESC LIMIT ?"
    params.append(limit)

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        click.echo(f"Search error: {e}")
        return

    if not results:
        click.echo("No bookmarks found.")
        return

    if format == 'json':
        click.echo(json.dumps(results, indent=2, default=str))

    elif format == 'urls':
        for bookmark in results:
            click.echo(bookmark['url'])

    else:  # table format
        click.echo(f"\nFound {len(results)} bookmarks:")
        click.echo("-" * 100)

        for bookmark in results:
            title = bookmark['title'][:60] + "..." if len(bookmark['title']) > 60 else bookmark['title']
            url = bookmark['url'][:50] + "..." if len(bookmark['url']) > 50 else bookmark['url']
            tags = bookmark['tags'][:30] + "..." if bookmark['tags'] and len(bookmark['tags']) > 30 else (bookmark['tags'] or '')

            click.echo(f"[{bookmark['id']}] {title}")
            click.echo(f"    URL: {url}")
            click.echo(f"    Domain: {bookmark['domain']} | Tags: {tags}")
            click.echo(f"    Created: {bookmark['created_at']}")
            click.echo("")


@cli.command()
@click.option('--url', '-u', required=True, help='Bookmark URL')
@click.option('--title', '-t', help='Bookmark title')
@click.option('--description', '-d', help='Bookmark description')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def add(ctx, url, title, description, tags):
    """Add a new bookmark."""
    db = ctx.obj['db']

    bookmark_data = {
        'url': url,
        'title': title or '',
        'description': description or '',
        'source': 'manual'
    }

    bookmark_id = db.insert_bookmark(bookmark_data)

    if bookmark_id:
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            db.add_bookmark_tags(bookmark_id, tag_list)

        click.echo(f"✅ Added bookmark {bookmark_id}: {title or url}")
    else:
        click.echo("❌ Failed to add bookmark (may already exist)")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    db = ctx.obj['db']

    stats = db.get_stats()

    click.echo("📊 Database Statistics:")
    click.echo("-" * 30)

    for key, value in stats.items():
        if isinstance(value, dict):
            click.echo(f"{key.replace('_', ' ').title()}:")
            for subkey, subvalue in value.items():
                click.echo(f"  {subkey}: {subvalue}")
        else:
            click.echo(f"{key.replace('_', ' ').title()}: {value}")


@cli.command()
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'yaml']),
              default='json', help='Export format')
@click.option('--tag', '-t', help='Filter by tag')
@click.pass_context
def export(ctx, output, format, tag):
    """Export bookmarks to various formats."""
    db = ctx.obj['db']

    # Build query
    query = """
        SELECT b.id, b.url, b.title, b.description, b.domain,
               b.created_at, b.source, GROUP_CONCAT(t.name, ',') as tags
        FROM bookmarks b
        LEFT JOIN bookmark_tags bt ON b.id = bt.bookmark_id
        LEFT JOIN tags t ON bt.tag_id = t.id
        WHERE b.status = 'active'
    """
    params = []

    if tag:
        query += """ AND b.id IN (
            SELECT bt.bookmark_id FROM bookmark_tags bt
            JOIN tags t ON bt.tag_id = t.id
            WHERE t.name LIKE ?
        )"""
        params.append(f"%{tag}%")

    query += " GROUP BY b.id ORDER BY b.created_at DESC"

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            bookmarks = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        click.echo(f"Export error: {e}")
        return

    if not bookmarks:
        click.echo("No bookmarks found to export.")
        return

    # Process tags
    for bookmark in bookmarks:
        if bookmark['tags']:
            bookmark['tags'] = [tag.strip() for tag in bookmark['tags'].split(',') if tag.strip()]
        else:
            bookmark['tags'] = []

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(bookmarks, f, indent=2, default=str)

        elif format == 'csv':
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if bookmarks:
                    writer = csv.DictWriter(f, fieldnames=bookmarks[0].keys())
                    writer.writeheader()
                    for bookmark in bookmarks:
                        # Convert tags list to string for CSV
                        bookmark['tags'] = ', '.join(bookmark['tags']) if bookmark['tags'] else ''
                        writer.writerow(bookmark)

        elif format == 'yaml':
            import yaml
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(bookmarks, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"✅ Exported {len(bookmarks)} bookmarks to {output_path}")

    else:
        # Print to stdout
        if format == 'json':
            click.echo(json.dumps(bookmarks, indent=2, default=str))
        else:
            click.echo("Specify --output for CSV/YAML export")


if __name__ == '__main__':
    cli()