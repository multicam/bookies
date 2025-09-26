'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { VirtualBookmarkList } from '@/components/bookmarks/virtual-bookmark-list'
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
      <Sidebar
        selectedTags={selectedTags}
        onTagsChange={setSelectedTags}
        onFilterChange={handleFilterChange}
      />

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
