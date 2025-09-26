'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { VirtualBookmarkList } from '@/components/bookmarks/virtual-bookmark-list'
import { useResizable } from '@/lib/hooks/use-resizable'
import type { ViewMode, SortConfig } from '@/lib/types'

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [filters, setFilters] = useState<any>({ status: 'active' })
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'createdAt',
    order: 'desc'
  })

  const { width: sidebarWidth, isResizing, startResize } = useResizable({
    initialWidth: 256,
    minWidth: 200,
    maxWidth: 600,
    storageKey: 'sidebar-width'
  })

  const handleFilterChange = (newFilters: any) => {
    setFilters(newFilters)
  }

  const handleAddBookmark = () => {
    // TODO: Open add bookmark dialog
    console.log('Add bookmark clicked')
  }

  const combinedFilters = {
    ...filters,
    tags: selectedTags.length > 0 ? selectedTags : undefined,
    search: searchQuery || undefined
  }

  return (
    <div className="flex h-screen bg-background">
      <div
        className="relative flex-shrink-0"
        style={{ width: sidebarWidth }}
      >
        <Sidebar
          selectedTags={selectedTags}
          onTagsChange={setSelectedTags}
          onFilterChange={handleFilterChange}
          className="h-full"
        />

        {/* Resize Handle */}
        <div
          className="absolute top-0 right-0 w-1 h-full cursor-col-resize bg-border hover:bg-primary/20 active:bg-primary/30 transition-colors"
          onMouseDown={startResize}
        />
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedTags={selectedTags}
          onTagsChange={setSelectedTags}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          sortConfig={sortConfig}
          onSortChange={setSortConfig}
          onAddBookmark={handleAddBookmark}
        />

        <main className="flex-1 overflow-hidden">
          <VirtualBookmarkList
            filters={combinedFilters}
            sort={sortConfig}
            viewMode={viewMode}
          />
        </main>
      </div>
    </div>
  )
}
