#!/usr/bin/env tsx

import { PrismaClient } from '@prisma/client'
import Database from 'better-sqlite3'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Initialize Prisma client for the new database
const prisma = new PrismaClient()

// Open the backup database using better-sqlite3
const backupDbPath = join(__dirname, '../../database/bookmarks.db.backup')
const backupDb = new Database(backupDbPath)

interface OldBookmark {
  id: number
  url: string
  title: string | null
  description: string | null
  domain: string | null
  url_hash: string
  created_at: string | null
  updated_at: string | null
  imported_at: string | null
  source: string
  source_file: string | null
  status: string | null
  favicon_url: string | null
  screenshot_url: string | null
  content_type: string | null
  language: string | null
  read_status: boolean | null
  favorite: boolean | null
}

interface OldTag {
  id: number
  name: string
  color: string | null
  created_at: string | null
  usage_count: number | null
}

interface OldBookmarkTag {
  bookmark_id: number
  tag_id: number
  created_at: string | null
}

async function migrateData() {
  console.log('🚀 Starting data migration...')

  try {
    // Get counts from backup database
    const bookmarkCount = backupDb.prepare('SELECT COUNT(*) as count FROM bookmarks').get() as { count: number }
    const tagCount = backupDb.prepare('SELECT COUNT(*) as count FROM tags').get() as { count: number }
    const bookmarkTagCount = backupDb.prepare('SELECT COUNT(*) as count FROM bookmark_tags').get() as { count: number }

    console.log(`📊 Found in backup database:`)
    console.log(`   - ${bookmarkCount.count} bookmarks`)
    console.log(`   - ${tagCount.count} tags`)
    console.log(`   - ${bookmarkTagCount.count} bookmark-tag relationships`)

    // 1. Migrate tags first
    console.log('📝 Migrating tags...')
    const oldTags = backupDb.prepare('SELECT * FROM tags ORDER BY id').all() as OldTag[]

    const tagMap = new Map<number, number>() // old_id -> new_id

    for (const oldTag of oldTags) {
      try {
        const newTag = await prisma.tag.create({
          data: {
            name: oldTag.name || '',
            color: oldTag.color || '#6B7280',
            createdAt: oldTag.created_at ? new Date(oldTag.created_at) : new Date(),
            usageCount: oldTag.usage_count || 0,
          }
        })
        tagMap.set(oldTag.id, newTag.id)
      } catch (error) {
        console.error(`Failed to migrate tag ${oldTag.id}: ${oldTag.name}`, error)
      }
    }
    console.log(`✅ Migrated ${tagMap.size}/${oldTags.length} tags`)

    // 2. Migrate bookmarks
    console.log('🔖 Migrating bookmarks...')
    const oldBookmarks = backupDb.prepare('SELECT * FROM bookmarks ORDER BY id').all() as OldBookmark[]

    const bookmarkMap = new Map<number, number>() // old_id -> new_id
    let migratedBookmarks = 0

    for (const oldBookmark of oldBookmarks) {
      try {
        // Clean and validate data
        const cleanUrl = oldBookmark.url?.trim() || ''
        const cleanTitle = oldBookmark.title?.trim() || ''
        const cleanDescription = oldBookmark.description?.trim() || null
        const cleanDomain = oldBookmark.domain?.trim() || null
        const cleanUrlHash = oldBookmark.url_hash?.trim() || ''

        if (!cleanUrl || !cleanUrlHash) {
          console.warn(`Skipping bookmark ${oldBookmark.id}: missing URL or hash`)
          continue
        }

        const newBookmark = await prisma.bookmark.create({
          data: {
            url: cleanUrl,
            title: cleanTitle,
            description: cleanDescription,
            domain: cleanDomain,
            urlHash: cleanUrlHash,
            createdAt: oldBookmark.created_at ? new Date(oldBookmark.created_at) : new Date(),
            updatedAt: oldBookmark.updated_at ? new Date(oldBookmark.updated_at) : new Date(),
            importedAt: oldBookmark.imported_at ? new Date(oldBookmark.imported_at) : new Date(),
            source: oldBookmark.source || 'unknown',
            sourceFile: oldBookmark.source_file,
            status: oldBookmark.status || 'active',
            faviconUrl: oldBookmark.favicon_url,
            screenshotUrl: oldBookmark.screenshot_url,
            contentType: oldBookmark.content_type,
            language: oldBookmark.language,
            readStatus: oldBookmark.read_status || false,
            favorite: oldBookmark.favorite || false,
          }
        })

        bookmarkMap.set(oldBookmark.id, newBookmark.id)
        migratedBookmarks++

        // Progress indicator
        if (migratedBookmarks % 1000 === 0) {
          console.log(`   Processed ${migratedBookmarks} bookmarks...`)
        }
      } catch (error) {
        console.error(`Failed to migrate bookmark ${oldBookmark.id}: ${oldBookmark.url}`, error)
      }
    }
    console.log(`✅ Migrated ${migratedBookmarks}/${oldBookmarks.length} bookmarks`)

    // 3. Migrate bookmark-tag relationships
    console.log('🔗 Migrating bookmark-tag relationships...')
    const oldBookmarkTags = backupDb.prepare('SELECT * FROM bookmark_tags').all() as OldBookmarkTag[]

    let migratedRelations = 0

    for (const oldRelation of oldBookmarkTags) {
      try {
        const newBookmarkId = bookmarkMap.get(oldRelation.bookmark_id)
        const newTagId = tagMap.get(oldRelation.tag_id)

        if (!newBookmarkId || !newTagId) {
          continue // Skip if either bookmark or tag wasn't migrated
        }

        await prisma.bookmarkTag.create({
          data: {
            bookmarkId: newBookmarkId,
            tagId: newTagId,
            createdAt: oldRelation.created_at ? new Date(oldRelation.created_at) : new Date(),
          }
        })

        migratedRelations++

        if (migratedRelations % 1000 === 0) {
          console.log(`   Processed ${migratedRelations} relationships...`)
        }
      } catch (error) {
        console.error(`Failed to migrate bookmark-tag relationship`, error)
      }
    }
    console.log(`✅ Migrated ${migratedRelations}/${oldBookmarkTags.length} bookmark-tag relationships`)

    // 4. Update tag usage counts
    console.log('🔄 Updating tag usage counts...')
    await prisma.$executeRaw`
      UPDATE tags
      SET usage_count = (
        SELECT COUNT(*)
        FROM bookmark_tags
        WHERE bookmark_tags.tag_id = tags.id
      )
    `

    // Final counts
    const finalBookmarkCount = await prisma.bookmark.count()
    const finalTagCount = await prisma.tag.count()
    const finalRelationCount = await prisma.bookmarkTag.count()

    console.log('\n🎉 Migration completed!')
    console.log(`📊 Final counts:`)
    console.log(`   - ${finalBookmarkCount} bookmarks`)
    console.log(`   - ${finalTagCount} tags`)
    console.log(`   - ${finalRelationCount} bookmark-tag relationships`)

  } catch (error) {
    console.error('❌ Migration failed:', error)
    process.exit(1)
  } finally {
    backupDb.close()
    await prisma.$disconnect()
  }
}

// Run migration
migrateData()
  .then(() => {
    console.log('✨ Data migration completed successfully!')
    process.exit(0)
  })
  .catch((error) => {
    console.error('💥 Migration failed:', error)
    process.exit(1)
  })