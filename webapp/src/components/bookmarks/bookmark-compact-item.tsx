'use client'

import { memo } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Star, Globe } from 'lucide-react'
import type { BookmarkWithTags } from '@/lib/types'
import { cn } from '@/lib/utils'

interface BookmarkCompactItemProps {
  bookmark: BookmarkWithTags
  isSelected?: boolean
  onSelect?: () => void
  className?: string
}

export const BookmarkCompactItem = memo(function BookmarkCompactItem({
  bookmark,
  isSelected = false,
  onSelect,
  className
}: BookmarkCompactItemProps) {
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
        'group flex items-center px-3 py-2 hover:bg-accent cursor-pointer border-l-2 transition-colors',
        isSelected ? 'border-l-primary bg-primary/5' : 'border-l-transparent',
        className
      )}
      onClick={handleClick}
    >
      {/* Favicon */}
      <div className="flex-shrink-0 mr-3">
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
      <div className="flex-1 min-w-0 mr-2">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium truncate flex-1">
            {bookmark.title || bookmark.url}
          </h4>

          {bookmark.favorite && (
            <Star className="w-3 h-3 text-yellow-500 fill-current flex-shrink-0" />
          )}
        </div>

        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground truncate">
            {bookmark.domain}
          </span>

          {tags.length > 0 && (
            <div className="flex gap-1">
              {tags.slice(0, 2).map((tag) => (
                <Badge key={tag.id} variant="secondary" className="text-2xs px-1 py-0">
                  {tag.name}
                </Badge>
              ))}
              {tags.length > 2 && (
                <span className="text-2xs text-muted-foreground">
                  +{tags.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex-shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          asChild
        >
          <a
            href={bookmark.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center"
          >
            <ExternalLink className="w-3 h-3" />
          </a>
        </Button>
      </div>

      {bookmark.readStatus && (
        <div className="w-2 h-2 rounded-full bg-green-600 ml-2 flex-shrink-0" />
      )}
    </div>
  )
})