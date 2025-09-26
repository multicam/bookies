# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Environment Context

- **Platform**: Linux (Ubuntu)
- **Shell**: bash 5.2.21(1)-release
- **Working Directory**: `/home/jean-marc/dev/bookies`
- **User Home**: `/home/jean-marc`
- **Repository Path**: `~/dev/bookies`

## Repository Overview

This repository serves as a personal bookmark and content curation system. It contains:
- Browser bookmark exports from various dates (2022-2025)
- RSS/Atom feed data (feed.xml)
- Raindrop.io bookmark exports
- Developer notes and resources

## Repository Structure

```
bookies/
├── data/
│   └── ingest/
│       ├── +++.md                    # Structured bookmarks with YAML metadata
│       ├── Dev Notes.md              # Development resources and notes
│       ├── index.md                  # Main index/entry file
│       ├── feed.xml                  # RSS/Atom feed data
│       ├── bookmarks_*.html          # Browser bookmark exports by date
│       ├── Raindrop.io-*.html        # Raindrop.io service exports
│       └── --db-feeds/               # Categorized bookmark feeds by topic
├── scripts/
│   ├── models/
│   │   └── database.py               # Database management and schema
│   ├── parsers/
│   │   ├── html_parser.py            # HTML bookmark file parser
│   │   ├── yaml_parser.py            # YAML structured bookmark parser
│   │   └── feed_processor.py         # Feed category processor
│   ├── utils/
│   │   ├── deduplication.py          # Bookmark deduplication engine
│   │   └── metadata_extractor.py     # Web metadata extraction
│   ├── cli.py                        # Command-line interface
│   └── run.py                        # Main CLI entry point
├── CLAUDE.md                         # Claude AI guidance
└── .gitignore                        # Git ignore file
```

## Content Types

### Bookmark Files
- **HTML files**: Browser bookmark exports named by date (e.g., `bookmarks_9_27_25.html`)
- **Raindrop exports**: Multiple HTML files from Raindrop.io bookmark service
- **Metadata format**: Standard Netscape bookmark format with favicon data

### Content Files
- **+++.md**: Contains bookmarks with structured metadata including IDs, URLs, creation dates, and tags
- **Dev Notes.md**: Curated list of development resources including:
  - Font resources (Google Fonts)
  - AI tools and prompting techniques
  - JavaScript frameworks (Svelte, TanStack Query)
  - Animation libraries
  - Development tools and products

### Feed Data
- **feed.xml**: Atom feed containing curated creative resources with author attribution and timestamps

## Quick Navigation

```bash
# Navigate to repository
cd ~/dev/bookies

# Navigate to data directory
cd data/ingest

# Return to repository root
cd ~/dev/bookies
```

## Common Workflows

### Adding New Bookmarks
1. Export bookmarks from browser to `data/ingest/bookmarks_MM_DD_YY.html`
2. For structured bookmarks, add entries to `data/ingest/+++.md`
3. Update development notes in `data/ingest/Dev Notes.md` if relevant
4. Commit changes with descriptive message

### Searching Across Collections
```bash
# Search for a specific technology or topic
grep -r -i "react" data/ingest/

# Search within specific file types
find data/ingest -name "*.html" -exec grep -l "keyword" {} \;

# Case-insensitive search across all bookmark files
grep -i -n "search-term" data/ingest/bookmarks_*.html
```

## Common Operations

### View Bookmark Collections
```bash
# List all bookmark files by date
ls -la data/ingest/bookmarks_*.html

# View recent bookmark exports
ls -t data/ingest/bookmarks_*.html | head -5

# Search for specific topics in bookmarks
grep -i "javascript" data/ingest/bookmarks_*.html
grep -i "design" data/ingest/*.md
```

### Analyze Content
```bash
# Count total bookmarks in HTML files
grep -c "<A HREF" data/ingest/bookmarks_*.html

# Extract URLs from bookmark files
grep -o 'HREF="[^"]*"' data/ingest/bookmarks_*.html | head -10

# View structured bookmark metadata
cat data/ingest/+++.md | grep -A 2 "^---"
```

### Check Feed Data
```bash
# View feed entries
xmllint --format data/ingest/feed.xml | head -50

# Count feed entries
grep -c "<entry>" data/ingest/feed.xml
```

### Content Management
```bash
# Find duplicate bookmarks across files
sort data/ingest/bookmarks_*.html | uniq -d

# Search for specific domains
grep -h "github.com" data/ingest/bookmarks_*.html data/ingest/*.md

# View development resources
cat data/ingest/"Dev Notes.md"
```

## CLI Tools

The repository includes a comprehensive command-line interface for bookmark management:

### Running the CLI
```bash
# From repository root
python scripts/run.py --help

# With verbose logging
python scripts/run.py --verbose stats

# Specify custom database location
python scripts/run.py --database /path/to/bookmarks.db stats
```

### Available Commands

#### Import Operations
```bash
# Import all bookmark sources
python scripts/run.py import-bookmarks

# Import only HTML browser exports
python scripts/run.py import-bookmarks --source html

# Import structured YAML bookmarks
python scripts/run.py import-bookmarks --source yaml

# Import categorized feeds
python scripts/run.py import-bookmarks --source feeds

# Import from specific directory
python scripts/run.py import-bookmarks --directory /path/to/bookmarks
```

#### Search and Discovery
```bash
# Search bookmark titles and content
python scripts/run.py search --query "javascript framework"

# Filter by tags
python scripts/run.py search --tag "design"

# Filter by domain
python scripts/run.py search --domain "github.com"

# Limit results and change format
python scripts/run.py search --query "react" --limit 10 --format json
```

#### Deduplication
```bash
# Generate deduplication report
python scripts/run.py deduplicate --report-only

# Run automatic deduplication
python scripts/run.py deduplicate --auto --similarity 0.9

# Interactive deduplication
python scripts/run.py deduplicate
```

#### Metadata Enrichment
```bash
# Enrich bookmarks with web metadata
python scripts/run.py enrich --batch-size 50 --max-workers 5

# Validate bookmark URLs
python scripts/run.py validate --batch-size 100
```

#### Data Management
```bash
# Add new bookmark manually
python scripts/run.py add --url "https://example.com" --title "Example" --tags "reference,tools"

# Show database statistics
python scripts/run.py stats

# Export bookmarks to various formats
python scripts/run.py export --format json --output bookmarks.json
python scripts/run.py export --format csv --tag "development"
python scripts/run.py export --format yaml --output dev-bookmarks.yaml
```

### CLI Architecture

The CLI system consists of:
- **Database Layer** (`models/database.py`): SQLite database management with FTS5 search
- **Parsers** (`parsers/`): HTML, YAML, and feed format processors
- **Utils** (`utils/`): Deduplication engine and metadata extraction
- **CLI Interface** (`cli.py`): Click-based command interface
- **Entry Point** (`run.py`): Main application launcher

**Recent Improvements**: All relative import issues have been resolved, and the CLI is fully functional. The system now uses absolute imports for better module resolution and reliability.

## Development Resources Available

This repository contains curated collections of:
- **UI/UX Tools**: Design systems, wireframing, mockup generators
- **Development Frameworks**: React, Svelte, TanStack Query, Node.js libraries
- **AI Resources**: Meta prompting techniques, ML tools, OpenAI cookbook
- **Animation Libraries**: CSS animations, scroll-driven animations
- **Performance Tools**: Testing frameworks, monitoring solutions
- **Typography**: Google Fonts integration guides
- **Database Tools**: SQL utilities, database administration tools

## File Formats and Standards

### Bookmark HTML Format
- Standard Netscape bookmark file format
- Includes favicon data as base64 encoded images
- Contains ADD_DATE timestamps and folder structures
- Preserves bookmark hierarchy and organization

### Structured Bookmarks (+++.md)
- YAML front matter with `id`, `url`, `created`, `tags`, `source` fields
- Entries separated by `---` dividers
- Sequential ID numbering system
- Example format:
  ```yaml
  ---
  id: 4066
  url: https://example.com
  created: 2023-01-01
  tags: [ux, design]
  source: manual
  ---
  ```

### XML Feed Format
- Atom 1.0 specification compliance
- Author attribution for each entry
- Timestamped entries with HTML content summaries
- Linked resources with full URLs

## Data Integrity

### Backup Pattern
Multiple bookmark exports suggest regular backup practices:
- Monthly exports from various browsers
- Service-specific exports (Raindrop.io)
- Incremental additions with date-based naming

### Content Verification
```bash
# Verify XML feed structure
xmllint --noout data/ingest/feed.xml && echo "Feed XML is valid"

# Check for broken markdown structure
grep -n "^---$" data/ingest/+++.md

# Validate bookmark HTML structure
head -5 data/ingest/bookmarks_*.html | grep DOCTYPE
```

## Git Operations

### Common Git Tasks
```bash
# Check repository status
git status

# Add new bookmark files
git add data/ingest/bookmarks_*.html

# Commit bookmark updates
git commit -m "Add bookmarks export from $(date +%m_%d_%y)"

# View recent changes
git log --oneline -10

# Show changes in bookmark files
git diff data/ingest/
```

### Repository Maintenance
```bash
# Check repository size
du -sh .

# List largest files
find . -type f -exec ls -lh {} \; | sort -k5 -hr | head -10

# Clean up old exports (be careful!)
# ls -t data/ingest/bookmarks_*.html | tail -n +6  # Shows files older than 5 most recent
```

## Useful Aliases

Add these to your `~/.bashrc` for quick access:
```bash
# Quick navigation
alias bookies="cd ~/dev/bookies"
alias bookiesdb="cd ~/dev/bookies/data/ingest"

# CLI shortcuts
alias bcli="cd ~/dev/bookies && python scripts/run.py"
alias bstats="cd ~/dev/bookies && python scripts/run.py stats"
alias bsearch='function _bsearch() { cd ~/dev/bookies && python scripts/run.py search --query "$1"; }; _bsearch'
alias bimport="cd ~/dev/bookies && python scripts/run.py import-bookmarks"
alias bdedup="cd ~/dev/bookies && python scripts/run.py deduplicate --report-only"

# Quick searches (traditional)
alias searchbooks='function _search() { grep -r -i "$1" ~/dev/bookies/data/ingest/; }; _search'
alias countbooks='grep -c "<A HREF" ~/dev/bookies/data/ingest/bookmarks_*.html'

# Quick git operations
alias bookiesstatus='cd ~/dev/bookies && git status'
alias bookieslog='cd ~/dev/bookies && git log --oneline -10'
```

This repository serves as a comprehensive personal knowledge base for web development, design, and technology resources, maintained through systematic bookmark curation and export practices. The integrated CLI tools provide powerful automation for importing, managing, searching, and maintaining bookmark collections with deduplication, metadata enrichment, and multiple export formats.
