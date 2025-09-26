# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal bookmark and content curation system that serves as a comprehensive knowledge base for web development, design, and technology resources. The system includes both raw data exports and a modern Next.js webapp for browsing and managing bookmarks.

### Components
- Browser bookmark exports spanning 2022-2025
- Structured bookmark metadata with IDs and tags
- Next.js webapp with React frontend and API routes
- Prisma ORM with SQLite database
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
├── webapp/                           # Next.js application
│   ├── src/
│   │   ├── app/                      # Next.js 15 app router
│   │   │   ├── api/                  # API routes (bookmarks, tags, search)
│   │   │   ├── layout.tsx            # Root layout with providers
│   │   │   └── page.tsx              # Main bookmark list page
│   │   ├── components/               # React components
│   │   │   ├── bookmarks/            # Bookmark-specific components
│   │   │   ├── layout/               # Layout components
│   │   │   └── ui/                   # Reusable UI components
│   │   └── lib/                      # Utilities and hooks
│   ├── prisma/
│   │   ├── schema.prisma             # Database schema
│   │   └── migrations/               # Database migrations
│   ├── scripts/
│   │   └── migrate-data.ts           # Data migration script
│   └── package.json                  # Dependencies and scripts
├── database/
│   └── bookmarks.db                  # SQLite database
└── WARP.md                          # WARP terminal guidance (reference)
```

## Webapp Technology Stack

- **Framework**: Next.js 15 with Turbopack
- **Frontend**: React 19 with TypeScript
- **Styling**: Tailwind CSS 4.0
- **Database**: SQLite with Prisma ORM
- **State Management**: TanStack Query for server state
- **UI Components**: Radix UI primitives
- **Virtualization**: TanStack Virtual for large lists
- **Icons**: Lucide React
- **Theming**: next-themes for dark/light mode

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


### Webapp Development
```bash
# Start development server (from webapp directory)
npm run dev

# Run type checking
npx tsc --noEmit

# Run linting
npm run lint

# Build for production
npm run build

# Generate Prisma client
npx prisma generate

# Apply database migrations
npx prisma migrate deploy

# Reset database and apply migrations
npx prisma migrate reset

# View database in Prisma Studio
npx prisma studio
```

### Content Analysis
```bash
# Search across all bookmark collections
grep -r -i "search-term" data/ingest/

# Count bookmarks in HTML files
grep -c "<A HREF" data/ingest/bookmarks_*.html

# Count bookmarks in database
sqlite3 database/bookmarks.db "SELECT COUNT(*) FROM bookmarks;"

# View recent bookmarks
sqlite3 database/bookmarks.db "SELECT title, url, created_at FROM bookmarks ORDER BY created_at DESC LIMIT 10;"

# Extract URLs from bookmarks
grep -o 'HREF="[^"]*"' data/ingest/bookmarks_*.html

# View structured bookmark metadata
grep -A 2 "^---" data/ingest/+++.md
```

### Content Management
```bash
# Find specific domains across collections
grep -h "github.com" data/ingest/bookmarks_*.html data/ingest/*.md

# Search bookmarks in database
sqlite3 database/bookmarks.db "SELECT title, url FROM bookmarks WHERE url LIKE '%github.com%';"

# Validate XML feed structure
xmllint --noout data/ingest/feed.xml

# Check markdown structure integrity
grep -n "^---$" data/ingest/+++.md

# Backup database
cp database/bookmarks.db database/bookmarks.db.backup
```

### Data Import Workflow
1. **Legacy HTML Import**: Export bookmarks to `data/ingest/bookmarks_MM_DD_YY.html`
2. **Structured Data**: Add entries to `data/ingest/+++.md` if needed
3. **Database Import**: Use migration scripts to import into SQLite database
4. **Development Resources**: Update `data/ingest/Dev Notes.md` for development resources
5. **Commit**: Use descriptive message including date

### Database Management
- **Current Database**: `database/bookmarks.db` (23,376 bookmarks, 194 tags)
- **Migration Script**: `webapp/scripts/migrate-data.ts` for importing legacy data
- **Schema**: Defined in `webapp/prisma/schema.prisma`
- **Backup Strategy**: Create `.backup` files before major operations

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

## Current Status (Updated 2025-09-27)

### Webapp Status
- ✅ **Development Server**: Running on port 3000 with Turbopack
- ✅ **TypeScript**: All type errors resolved
- ✅ **ESLint**: All code quality issues fixed
- ✅ **API Endpoints**: All returning data correctly
- ✅ **Database**: Clean migration completed successfully

### Recent Fixes Applied
1. **Import Error Fix**: Corrected `useBookmarks` to `useInfiniteBookmarks` in `virtual-bookmark-list.tsx`
2. **Next.js 15 Compatibility**: Updated API routes for async params handling
3. **Prisma Query Issues**: Removed invalid `mode: 'insensitive'` properties
4. **Database Migration**: Successfully migrated 23,376 bookmarks with 99.97% success rate

### Known Working Features
- Infinite scrolling bookmark list with virtualization
- Search functionality across titles, descriptions, and URLs
- Tag filtering and management
- Responsive design with dark/light theme support
- Real-time bookmark count and statistics

## Development Notes

This repository follows a systematic curation approach with multiple export formats to ensure comprehensive bookmark preservation and easy content discovery across years of collected resources. The webapp provides a modern interface for browsing and managing the bookmark collection with full-text search and tag-based organization.
