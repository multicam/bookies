'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import type { BookmarkWithTags } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Search,
  Plus,
  Filter,
  Settings,
  Moon,
  Sun,
  BookmarkPlus,
  MoreVertical,
  Grid3X3,
  List,
  Columns,
  LayoutGrid,
  SortDesc,
  SortAsc
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { useSearchBookmarks } from '@/lib/hooks/use-bookmarks'
import { useTags } from '@/lib/hooks/use-tags'
import type { ViewMode, SortConfig } from '@/lib/types'

interface HeaderProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  sortConfig: SortConfig
  onSortChange: (sort: SortConfig) => void
  onAddBookmark?: () => void
}

export function Header({
  searchQuery,
  onSearchChange,
  selectedTags,
  onTagsChange,
  viewMode,
  onViewModeChange,
  sortConfig,
  onSortChange,
  onAddBookmark
}: HeaderProps) {
  const { theme, setTheme } = useTheme()
  const [isTagsOpen, setIsTagsOpen] = useState(false)

  const { data: searchResults } = useSearchBookmarks(searchQuery, searchQuery.length >= 2)
  const { data: allTags = [] } = useTags('', true)

  const handleTagSelect = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      onTagsChange(selectedTags.filter(t => t !== tagName))
    } else {
      onTagsChange([...selectedTags, tagName])
    }
  }

  const clearAllTags = () => {
    onTagsChange([])
  }

  const viewModeIcons = {
    list: List,
    grid: LayoutGrid,
    card: Columns,
    compact: Grid3X3,
  }

  const sortOptions = [
    { field: 'createdAt' as const, label: 'Date Added' },
    { field: 'updatedAt' as const, label: 'Last Modified' },
    { field: 'title' as const, label: 'Title' },
    { field: 'domain' as const, label: 'Domain' },
  ]

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center gap-4 px-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <BookmarkPlus className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">Bookies</h1>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search bookmarks..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />

          {/* Quick search results */}
          {searchResults?.results && searchQuery.length >= 2 && (
            <div className="absolute top-full mt-1 w-full bg-background border rounded-md shadow-lg max-h-64 overflow-y-auto z-50">
              {searchResults.results.bookmarks.slice(0, 5).map((bookmark: BookmarkWithTags) => (
                <div
                  key={bookmark.id}
                  className="p-2 hover:bg-accent cursor-pointer border-b last:border-b-0"
                >
                  <div className="font-medium text-sm truncate">{bookmark.title}</div>
                  <div className="text-xs text-muted-foreground truncate">{bookmark.domain}</div>
                </div>
              ))}
              {searchResults.results.bookmarks.length === 0 && (
                <div className="p-4 text-center text-muted-foreground">No results found</div>
              )}
            </div>
          )}
        </div>

        {/* Selected Tags */}
        {selectedTags.length > 0 && (
          <div className="flex items-center gap-1">
            {selectedTags.slice(0, 3).map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="cursor-pointer"
                onClick={() => handleTagSelect(tag)}
              >
                {tag} ×
              </Badge>
            ))}
            {selectedTags.length > 3 && (
              <Badge variant="outline">
                +{selectedTags.length - 3}
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllTags}
              className="h-6 px-2 text-xs"
            >
              Clear
            </Button>
          </div>
        )}

        {/* Filter by Tags */}
        <Popover open={isTagsOpen} onOpenChange={setIsTagsOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-1" />
              Tags
              {selectedTags.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {selectedTags.length}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64 p-0">
            <Command>
              <CommandInput placeholder="Search tags..." />
              <CommandList>
                <CommandEmpty>No tags found.</CommandEmpty>
                <CommandGroup>
                  {allTags.slice(0, 20).map((tag) => (
                    <CommandItem
                      key={tag.id}
                      value={tag.name}
                      onSelect={() => handleTagSelect(tag.name)}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className={selectedTags.includes(tag.name) ? 'font-medium' : ''}>
                          {tag.name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {tag._count?.bookmarks || tag.usageCount}
                        </span>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>

        {/* View Mode */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              {(() => {
                const Icon = viewModeIcons[viewMode]
                return <Icon className="h-4 w-4" />
              })()}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {Object.entries(viewModeIcons).map(([mode, Icon]) => (
              <DropdownMenuItem
                key={mode}
                onClick={() => onViewModeChange(mode as ViewMode)}
                className={viewMode === mode ? 'bg-accent' : ''}
              >
                <Icon className="h-4 w-4 mr-2" />
                <span className="capitalize">{mode}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Sort */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              {sortConfig.order === 'asc' ? (
                <SortAsc className="h-4 w-4" />
              ) : (
                <SortDesc className="h-4 w-4" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {sortOptions.map((option) => (
              <DropdownMenuItem
                key={option.field}
                onClick={() => onSortChange({
                  field: option.field,
                  order: sortConfig.field === option.field && sortConfig.order === 'desc' ? 'asc' : 'desc'
                })}
                className={sortConfig.field === option.field ? 'bg-accent' : ''}
              >
                {option.label}
                {sortConfig.field === option.field && (
                  <span className="ml-2 text-xs">
                    ({sortConfig.order === 'asc' ? '↑' : '↓'})
                  </span>
                )}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Add Bookmark */}
        <Button onClick={onAddBookmark} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Add
        </Button>

        {/* More Options */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? (
                <>
                  <Sun className="h-4 w-4 mr-2" />
                  Light Mode
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4 mr-2" />
                  Dark Mode
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}