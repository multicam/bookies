'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  BookmarkIcon,
  Star,
  Archive,
  Tag,
  TrendingUp,
  Calendar,
  Globe,
  ChevronRight,
  ChevronDown,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useTags } from '@/lib/hooks/use-tags'
import { cn } from '@/lib/utils'

interface SidebarProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  onFilterChange: (filter: any) => void
  className?: string
}

export function Sidebar({ selectedTags, onTagsChange, onFilterChange, className }: SidebarProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['overview', 'quick-filters', 'top-tags'])
  )

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await fetch('/api/stats')
      if (!response.ok) throw new Error('Failed to fetch stats')
      return response.json()
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: topTags = [] } = useTags('', true)

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const handleTagClick = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      onTagsChange(selectedTags.filter(t => t !== tagName))
    } else {
      onTagsChange([...selectedTags, tagName])
    }
  }

  const quickFilters = [
    {
      id: 'all',
      label: 'All Bookmarks',
      icon: BookmarkIcon,
      count: stats?.overview.active || 0,
      filter: { status: 'active' }
    },
    {
      id: 'favorites',
      label: 'Favorites',
      icon: Star,
      count: stats?.overview.favorites || 0,
      filter: { status: 'active', favorite: true }
    },
    {
      id: 'unread',
      label: 'Unread',
      icon: Clock,
      count: stats?.overview.unread || 0,
      filter: { status: 'active', readStatus: false }
    },
    {
      id: 'read',
      label: 'Read',
      icon: CheckCircle2,
      count: stats?.overview.read || 0,
      filter: { status: 'active', readStatus: true }
    },
    {
      id: 'archived',
      label: 'Archived',
      icon: Archive,
      count: stats?.overview.archived || 0,
      filter: { status: 'ARCHIVED' }
    },
    {
      id: 'broken',
      label: 'Broken Links',
      icon: AlertTriangle,
      count: stats?.overview.broken || 0,
      filter: { status: 'BROKEN' }
    }
  ]

  return (
    <div className={cn("w-64 border-r bg-muted/10", className)}>
      <ScrollArea className="h-full">
        <div className="p-4 space-y-4">

          {/* Overview Stats */}
          <Collapsible
            open={expandedSections.has('overview')}
            onOpenChange={() => toggleSection('overview')}
          >
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-accent rounded-md">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="font-medium">Overview</span>
              </div>
              {expandedSections.has('overview') ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="p-2 bg-accent/50 rounded text-center">
                  <div className="font-semibold">{stats?.overview.total?.toLocaleString() || 0}</div>
                  <div className="text-muted-foreground text-xs">Total</div>
                </div>
                <div className="p-2 bg-accent/50 rounded text-center">
                  <div className="font-semibold">{stats?.overview.tags?.toLocaleString() || 0}</div>
                  <div className="text-muted-foreground text-xs">Tags</div>
                </div>
              </div>

              {stats?.health && (
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>Read Progress</span>
                    <span>{stats.health.readPercentage}%</span>
                  </div>
                  <div className="w-full bg-accent/30 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{ width: `${stats.health.readPercentage}%` }}
                    />
                  </div>
                </div>
              )}
            </CollapsibleContent>
          </Collapsible>

          {/* Quick Filters */}
          <Collapsible
            open={expandedSections.has('quick-filters')}
            onOpenChange={() => toggleSection('quick-filters')}
          >
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-accent rounded-md">
              <div className="flex items-center gap-2">
                <BookmarkIcon className="h-4 w-4" />
                <span className="font-medium">Quick Filters</span>
              </div>
              {expandedSections.has('quick-filters') ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-1">
              {quickFilters.map((filter) => (
                <Button
                  key={filter.id}
                  variant="ghost"
                  className="w-full justify-between h-8 px-2"
                  onClick={() => onFilterChange(filter.filter)}
                >
                  <div className="flex items-center gap-2">
                    <filter.icon className="h-4 w-4" />
                    <span className="text-sm">{filter.label}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {filter.count.toLocaleString()}
                  </Badge>
                </Button>
              ))}
            </CollapsibleContent>
          </Collapsible>

          {/* Top Tags */}
          <Collapsible
            open={expandedSections.has('top-tags')}
            onOpenChange={() => toggleSection('top-tags')}
          >
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-accent rounded-md">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4" />
                <span className="font-medium">Popular Tags</span>
              </div>
              {expandedSections.has('top-tags') ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-1">
              {topTags.slice(0, 15).map((tag) => (
                <Button
                  key={tag.id}
                  variant="ghost"
                  className={cn(
                    "w-full justify-between h-8 px-2",
                    selectedTags.includes(tag.name) && "bg-primary/10 text-primary"
                  )}
                  onClick={() => handleTagClick(tag.name)}
                >
                  <span className="text-sm truncate">{tag.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {tag._count?.bookmarks || tag.usageCount}
                  </Badge>
                </Button>
              ))}
            </CollapsibleContent>
          </Collapsible>

          {/* Top Domains */}
          {stats?.topDomains && stats.topDomains.length > 0 && (
            <Collapsible
              open={expandedSections.has('top-domains')}
              onOpenChange={() => toggleSection('top-domains')}
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-accent rounded-md">
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  <span className="font-medium">Top Domains</span>
                </div>
                {expandedSections.has('top-domains') ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 space-y-1">
                {stats.topDomains.slice(0, 10).map((domain: any) => (
                  <Button
                    key={domain.domain}
                    variant="ghost"
                    className="w-full justify-between h-8 px-2"
                    onClick={() => onFilterChange({ domains: [domain.domain] })}
                  >
                    <span className="text-sm truncate">{domain.domain}</span>
                    <Badge variant="secondary" className="text-xs">
                      {domain.count}
                    </Badge>
                  </Button>
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}

          {/* Sources */}
          {stats?.bySource && stats.bySource.length > 0 && (
            <Collapsible
              open={expandedSections.has('sources')}
              onOpenChange={() => toggleSection('sources')}
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-accent rounded-md">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  <span className="font-medium">Sources</span>
                </div>
                {expandedSections.has('sources') ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 space-y-1">
                {stats.bySource.map((source: any) => (
                  <div key={source.source} className="flex items-center justify-between px-2 py-1">
                    <span className="text-sm capitalize">
                      {source.source.replace('_', ' ')}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {source.count.toLocaleString()}
                    </Badge>
                  </div>
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}