# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal bookmark and content curation system that serves as a comprehensive knowledge base for web development, design, and technology resources. The repository contains:

- Browser bookmark exports spanning 2022-2025
- Structured bookmark metadata with IDs and tags
- Development resource collections
- RSS/Atom feed data
- Raindrop.io bookmark service exports

## Architecture

```
bookies/
├── data/
│   └── ingest/
│       ├── +++.md                    # Structured bookmarks with metadata (YAML front matter)
│       ├── Dev Notes.md              # Curated development resources
│       ├── index.md                  # Main index file
│       ├── feed.xml                  # Atom feed with timestamped entries
│       ├── bookmarks_*.html          # Browser exports (Netscape format)
│       ├── Raindrop.io-*.html        # Raindrop.io service exports
│       └── --db-feeds/               # Categorized bookmark feeds by topic
└── WARP.md                          # WARP terminal guidance (reference)
```

## Data Formats

### Structured Bookmarks (+++.md)
- YAML front matter with `id`, `url`, `created`, `tags`, `source` fields
- Entries separated by `---` dividers
- Sequential ID numbering system
- Example:
  ```yaml
  ---
  id: 4066
  url: https://example.com
  created: 2023-01-01
  tags: [ux, design]
  source: manual
  ---
  ```

### Bookmark HTML Files
- Standard Netscape bookmark format with ADD_DATE timestamps
- Contains base64 encoded favicon data
- Preserves folder hierarchy and bookmark organization
- Named by export date: `bookmarks_MM_DD_YY.html`

### Feed Data (feed.xml)
- Atom 1.0 specification compliant
- Author attribution and timestamped entries
- HTML content summaries with full URLs

## Common Operations

### Preliminaries

You run in an environment where `ast-grep` is available; whenever a search requires syntax-aware or structural matching, default to `ast-grep --lang rust -p '<pattern>'` (or set `--lang` appropriately) and avoid falling back to text-only tools like `rg` or `grep` unless I explicitly request a plain-text search.


### Content Analysis
```bash
# Search across all bookmark collections
grep -r -i "search-term" data/ingest/

# Count bookmarks in HTML files
grep -c "<A HREF" data/ingest/bookmarks_*.html

# Extract URLs from bookmarks
grep -o 'HREF="[^"]*"' data/ingest/bookmarks_*.html

# View structured bookmark metadata
grep -A 2 "^---" data/ingest/+++.md
```

### Content Management
```bash
# Find specific domains across collections
grep -h "github.com" data/ingest/bookmarks_*.html data/ingest/*.md

# Validate XML feed structure
xmllint --noout data/ingest/feed.xml

# Check markdown structure integrity
grep -n "^---$" data/ingest/+++.md
```

### Bookmark Addition Workflow
1. Export bookmarks to `data/ingest/bookmarks_MM_DD_YY.html`
2. Add structured entries to `data/ingest/+++.md` if needed
3. Update `data/ingest/Dev Notes.md` for development resources
4. Commit with descriptive message including date

## Development Resources

The repository contains curated collections of:
- **UI/UX Tools**: Design systems, wireframing, mockup generators
- **Development Frameworks**: React, Svelte, TanStack Query, Node.js libraries
- **AI Resources**: Meta prompting techniques, ML tools, OpenAI cookbook
- **Animation Libraries**: CSS animations, scroll-driven animations
- **Performance Tools**: Testing frameworks, monitoring solutions
- **Typography**: Google Fonts integration guides

## File Integrity

### Backup Pattern
- Regular bookmark exports with date-based naming
- Multiple browser sources and service exports
- Incremental content additions over time

### Data Verification
```bash
# Verify feed XML validity
xmllint --format data/ingest/feed.xml | head -50

# Check for duplicate bookmarks
sort data/ingest/bookmarks_*.html | uniq -d

# Validate bookmark HTML structure
head -5 data/ingest/bookmarks_*.html | grep DOCTYPE
```

This repository follows a systematic curation approach with multiple export formats to ensure comprehensive bookmark preservation and easy content discovery across years of collected resources.
