'use client'

import { memo } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Star, Calendar, Globe } from 'lucide-react'
import { format } from 'date-fns'
import type { BookmarkWithTags } from '@/lib/types'
import { cn } from '@/lib/utils'

interface BookmarkListItemProps {
  bookmark: BookmarkWithTags
  isSelected?: boolean
  onSelect?: () => void
  className?: string
}

export const BookmarkListItem = memo(function BookmarkListItem({
  bookmark,
  isSelected = false,
  onSelect,
  className
}: BookmarkListItemProps) {
  const tags = bookmark.tags.map(bt => bt.tag)

  const handleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('a, button')) {
      return
    }
    onSelect?.()
  }

  return (
    <div
      className={cn(
        'group p-4 border rounded-lg cursor-pointer transition-all hover:shadow-sm border-2',
        isSelected ? 'border-primary bg-primary/5' : 'border-transparent hover:border-border',
        className
      )}
      onClick={handleClick}
    >
      <div className="flex items-start gap-3">
        {/* Favicon */}
        <div className="flex-shrink-0 mt-1">
          {bookmark.faviconUrl ? (
            <img
              src={bookmark.faviconUrl}
              alt=""
              className="w-4 h-4"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          ) : (
            <Globe className="w-4 h-4 text-muted-foreground" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate">
                {bookmark.title || bookmark.url}
              </h3>
              <p className="text-sm text-muted-foreground truncate">
                {bookmark.domain}
              </p>
            </div>

            <div className="flex items-center gap-1 flex-shrink-0">
              {bookmark.favorite && (
                <Star className="w-4 h-4 text-yellow-500 fill-current" />
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                asChild
              >
                <a
                  href={bookmark.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </Button>
            </div>
          </div>

          {bookmark.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {bookmark.description}
            </p>
          )}

          <div className="flex items-center justify-between gap-4">
            {/* Tags */}
            <div className="flex flex-wrap gap-1 min-w-0">
              {tags.slice(0, 4).map((tag) => (
                <Badge key={tag.id} variant="secondary" className="text-xs">
                  {tag.name}
                </Badge>
              ))}
              {tags.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{tags.length - 4}
                </Badge>
              )}
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-3 text-xs text-muted-foreground flex-shrink-0">
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{bookmark.createdAt ? format(new Date(bookmark.createdAt), 'MMM d') : 'No date'}</span>
              </div>

              {bookmark.readStatus && (
                <div className="flex items-center gap-1 text-green-600">
                  <div className="w-2 h-2 rounded-full bg-green-600" />
                  <span>Read</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
})