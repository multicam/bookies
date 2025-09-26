'use client'

import { useVirtualizer } from '@tanstack/react-virtual'
import { useRef, useMemo } from 'react'
import type { BookmarkWithTags, ViewMode } from '@/lib/types'
import { BookmarkCard } from './bookmark-card'
import { BookmarkListItem } from './bookmark-list-item'
import { BookmarkCompactItem } from './bookmark-compact-item'

interface VirtualBookmarkListProps {
  bookmarks: BookmarkWithTags[]
  viewMode: ViewMode
  isLoading?: boolean
  hasMore?: boolean
  onLoadMore?: () => void
  onBookmarkSelect?: (bookmark: BookmarkWithTags) => void
  selectedBookmarks?: Set<number>
  className?: string
}

export function VirtualBookmarkList({
  bookmarks,
  viewMode,
  isLoading = false,
  hasMore = false,
  onLoadMore,
  onBookmarkSelect,
  selectedBookmarks = new Set(),
  className = ''
}: VirtualBookmarkListProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  // Calculate item size based on view mode
  const estimateSize = useMemo(() => {
    switch (viewMode) {
      case 'compact':
        return 60
      case 'list':
        return 120
      case 'card':
        return 280
      case 'grid':
        return 320
      default:
        return 120
    }
  }, [viewMode])

  const virtualizer = useVirtualizer({
    count: bookmarks.length + (hasMore ? 1 : 0), // Add 1 for loading indicator
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan: 5,
  })

  // Load more when approaching the end
  const lastItem = virtualizer.getVirtualItems().slice(-1)[0]
  if (lastItem && lastItem.index >= bookmarks.length - 3 && hasMore && !isLoading && onLoadMore) {
    onLoadMore()
  }

  const renderBookmarkItem = (bookmark: BookmarkWithTags, index: number) => {
    const isSelected = selectedBookmarks.has(bookmark.id)

    switch (viewMode) {
      case 'compact':
        return (
          <BookmarkCompactItem
            key={`${bookmark.id}-${index}`}
            bookmark={bookmark}
            isSelected={isSelected}
            onSelect={() => onBookmarkSelect?.(bookmark)}
          />
        )
      case 'list':
        return (
          <BookmarkListItem
            key={`${bookmark.id}-${index}`}
            bookmark={bookmark}
            isSelected={isSelected}
            onSelect={() => onBookmarkSelect?.(bookmark)}
          />
        )
      case 'card':
      case 'grid':
        return (
          <BookmarkCard
            key={`${bookmark.id}-${index}`}
            bookmark={bookmark}
            isSelected={isSelected}
            onSelect={() => onBookmarkSelect?.(bookmark)}
            variant={viewMode === 'grid' ? 'compact' : 'default'}
          />
        )
      default:
        return (
          <BookmarkListItem
            key={`${bookmark.id}-${index}`}
            bookmark={bookmark}
            isSelected={isSelected}
            onSelect={() => onBookmarkSelect?.(bookmark)}
          />
        )
    }
  }

  const getContainerClass = () => {
    const base = "w-full"

    switch (viewMode) {
      case 'grid':
        return `${base} grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4`
      case 'card':
        return `${base} space-y-4`
      case 'list':
        return `${base} space-y-2`
      case 'compact':
        return `${base} space-y-1`
      default:
        return `${base} space-y-2`
    }
  }

  if (viewMode === 'grid') {
    // Grid view uses a different approach due to CSS Grid
    return (
      <div
        ref={parentRef}
        className={`h-full overflow-auto ${className}`}
        style={{
          contain: 'strict',
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4">
          {bookmarks.map((bookmark, index) => renderBookmarkItem(bookmark, index))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="col-span-full flex items-center justify-center py-8">
              <div className="animate-spin h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Virtual scrolling for list views
  return (
    <div
      ref={parentRef}
      className={`h-full overflow-auto ${className}`}
      style={{
        contain: 'strict',
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const index = virtualItem.index
          const isLoaderRow = index >= bookmarks.length

          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {isLoaderRow ? (
                // Loading indicator
                isLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="animate-spin h-6 w-6 border-b-2 border-primary"></div>
                  </div>
                ) : null
              ) : (
                renderBookmarkItem(bookmarks[index], index)
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}