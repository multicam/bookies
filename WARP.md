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
│   └── db/
│       ├── +++.md                    # Special bookmarks with metadata
│       ├── Dev Notes.md              # Development resources and notes
│       ├── index.md                  # Main index/entry file
│       ├── feed.xml                  # RSS/Atom feed data
│       └── *.html                    # Browser bookmark exports by date
└── .gitignore                        # Git ignore file (excludes .idea/)
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

## Development Resources Available

This repository contains curated links to:
- **UI/UX Tools**: Design systems, wireframing tools, mockup generators
- **Development Frameworks**: React, Svelte, Node.js libraries
- **AI Resources**: Prompting guides, ML tools and platforms
- **Animation Libraries**: CSS animation tools and JavaScript libraries
- **Performance Tools**: Testing frameworks, monitoring solutions
- **Database Tools**: SQL utilities, database administration tools

## File Formats and Standards

### Bookmark HTML Format
- Standard Netscape bookmark file format
- Includes favicon data as base64 encoded images
- Contains ADD_DATE timestamps and folder structures
- Preserves bookmark hierarchy and organization

### Markdown Metadata Format
- YAML front matter with id, url, created date, tags, and source
- Structured content blocks separated by `---`
- Links to original sources and references

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

# Quick searches
alias searchbooks='function _search() { grep -r -i "$1" ~/dev/bookies/data/ingest/; }; _search'
alias countbooks='grep -c "<A HREF" ~/dev/bookies/data/ingest/bookmarks_*.html'

# Quick git operations
alias bookiesstatus='cd ~/dev/bookies && git status'
alias bookieslog='cd ~/dev/bookies && git log --oneline -10'
```

This repository serves as a comprehensive personal knowledge base for web development, design, and technology resources, maintained through systematic bookmark curation and export practices.
