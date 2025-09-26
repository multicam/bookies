import type { Bookmark, Tag, Collection } from '@prisma/client'

// Enhanced types with relations
export type BookmarkWithTags = Bookmark & {
  tags: Array<{
    tag: Tag
  }>
}

export type BookmarkWithRelations = Bookmark & {
  tags: Array<{
    tag: Tag
  }>
  collections: Array<{
    collection: Collection
  }>
}

// Search and filter types
export interface BookmarkFilters {
  query?: string
  tags?: string[]
  collections?: string[]
  domains?: string[]
  status?: string
  favorite?: boolean
  readStatus?: boolean
  dateRange?: {
    from?: Date
    to?: Date
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

// View modes for bookmark display
export type ViewMode = 'list' | 'grid' | 'card' | 'compact'

// Sort options
export type SortField = 'createdAt' | 'updatedAt' | 'title' | 'domain'
export type SortOrder = 'asc' | 'desc'

export interface SortConfig {
  field: SortField
  order: SortOrder
}

// Tag with usage stats
export type TagWithStats = Tag & {
  _count: {
    bookmarks: number
  }
}

// Collection with bookmark count
export type CollectionWithStats = Collection & {
  _count: {
    bookmarks: number
  }
  children?: CollectionWithStats[]
}