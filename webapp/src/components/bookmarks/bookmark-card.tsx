'use client'

import { memo } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Star, Bookmark, Calendar, Globe } from 'lucide-react'
import { format } from 'date-fns'
import type { BookmarkWithTags } from '@/lib/types'
import { cn } from '@/lib/utils'

interface BookmarkCardProps {
  bookmark: BookmarkWithTags
  isSelected?: boolean
  onSelect?: () => void
  variant?: 'default' | 'compact'
  className?: string
}

export const BookmarkCard = memo(function BookmarkCard({
  bookmark,
  isSelected = false,
  onSelect,
  variant = 'default',
  className
}: BookmarkCardProps) {
  const tags = bookmark.tags.map(bt => bt.tag)

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger selection when clicking on links or buttons
    if ((e.target as HTMLElement).closest('a, button')) {
      return
    }
    onSelect?.()
  }

  return (
    <Card
      className={cn(
        'group cursor-pointer transition-all hover:shadow-md border-2',
        isSelected ? 'border-primary bg-primary/5' : 'border-transparent hover:border-border',
        variant === 'compact' && 'h-64',
        className
      )}
      onClick={handleCardClick}
    >
      <CardHeader className={cn(
        'pb-3',
        variant === 'compact' && 'pb-2'
      )}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {bookmark.faviconUrl && (
                <img
                  src={bookmark.faviconUrl}
                  alt=""
                  className="w-4 h-4 flex-shrink-0"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
              )}
              <span className="text-sm text-muted-foreground truncate">
                {bookmark.domain}
              </span>
            </div>

            <h3 className={cn(
              'font-semibold leading-tight line-clamp-2',
              variant === 'compact' ? 'text-sm' : 'text-base'
            )}>
              {bookmark.title || bookmark.url}
            </h3>
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
      </CardHeader>

      <CardContent className="pt-0 space-y-3">
        {bookmark.description && (
          <p className={cn(
            'text-muted-foreground leading-relaxed',
            variant === 'compact' ? 'text-xs line-clamp-2' : 'text-sm line-clamp-3'
          )}>
            {bookmark.description}
          </p>
        )}

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.slice(0, variant === 'compact' ? 3 : 5).map((tag) => (
              <Badge
                key={tag.id}
                variant="secondary"
                className={cn(
                  "text-xs",
                  variant === 'compact' && 'text-2xs px-1.5 py-0.5'
                )}
              >
                {tag.name}
              </Badge>
            ))}
            {tags.length > (variant === 'compact' ? 3 : 5) && (
              <Badge variant="outline" className="text-xs">
                +{tags.length - (variant === 'compact' ? 3 : 5)}
              </Badge>
            )}
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{format(new Date(bookmark.createdAt), 'MMM d, yyyy')}</span>
            </div>
            {bookmark.source !== 'manual' && (
              <div className="flex items-center gap-1">
                <Bookmark className="w-3 h-3" />
                <span className="capitalize">{bookmark.source.replace('_', ' ')}</span>
              </div>
            )}
          </div>

          {bookmark.readStatus && (
            <div className="flex items-center gap-1 text-green-600">
              <div className="w-2 h-2 rounded-full bg-green-600" />
              <span>Read</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
})