import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  try {
    // Get basic counts
    const [
      totalBookmarks,
      activeBookmarks,
      archivedBookmarks,
      brokenBookmarks,
      totalTags,
      favoriteBookmarks,
      readBookmarks
    ] = await Promise.all([
      prisma.bookmark.count(),
      prisma.bookmark.count({ where: { status: 'active' } }),
      prisma.bookmark.count({ where: { status: 'ARCHIVED' } }),
      prisma.bookmark.count({ where: { status: 'BROKEN' } }),
      prisma.tag.count(),
      prisma.bookmark.count({ where: { favorite: true, status: 'active' } }),
      prisma.bookmark.count({ where: { readStatus: true, status: 'active' } })
    ])

    // Get bookmarks by source
    const bySource = await prisma.bookmark.groupBy({
      by: ['source'],
      where: { status: 'active' },
      _count: {
        id: true
      },
      orderBy: {
        _count: {
          id: 'desc'
        }
      }
    })

    // Get top domains
    const topDomains = await prisma.bookmark.groupBy({
      by: ['domain'],
      where: { status: 'active' },
      _count: {
        id: true
      },
      orderBy: {
        _count: {
          id: 'desc'
        }
      },
      take: 10
    })

    // Get top tags
    const topTags = await prisma.tag.findMany({
      where: {
        bookmarks: {
          some: {
            bookmark: {
              status: 'active'
            }
          }
        }
      },
      include: {
        _count: {
          select: {
            bookmarks: {
              where: {
                bookmark: {
                  status: 'active'
                }
              }
            }
          }
        }
      },
      orderBy: {
        usageCount: 'desc'
      },
      take: 10
    })

    // Get recent bookmarks count by day (last 30 days)
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const recentBookmarks = await prisma.bookmark.findMany({
      where: {
        createdAt: {
          gte: thirtyDaysAgo
        },
        status: 'active'
      },
      select: {
        createdAt: true
      },
      orderBy: {
        createdAt: 'desc'
      }
    })

    // Group by date for chart data
    const bookmarksByDate: { [key: string]: number } = {}
    recentBookmarks.forEach(bookmark => {
      if (bookmark.createdAt) {
        const date = bookmark.createdAt.toISOString().split('T')[0]
        bookmarksByDate[date] = (bookmarksByDate[date] || 0) + 1
      }
    })

    // Get oldest and newest bookmarks
    const [oldestBookmark, newestBookmark] = await Promise.all([
      prisma.bookmark.findFirst({
        where: { status: 'active' },
        orderBy: { createdAt: 'asc' },
        select: { createdAt: true }
      }),
      prisma.bookmark.findFirst({
        where: { status: 'active' },
        orderBy: { createdAt: 'desc' },
        select: { createdAt: true }
      })
    ])

    const stats = {
      overview: {
        total: totalBookmarks,
        active: activeBookmarks,
        archived: archivedBookmarks,
        broken: brokenBookmarks,
        tags: totalTags,
        favorites: favoriteBookmarks,
        read: readBookmarks,
        unread: activeBookmarks - readBookmarks
      },
      bySource: bySource.map(item => ({
        source: item.source,
        count: item._count.id
      })),
      topDomains: topDomains.map(item => ({
        domain: item.domain || 'Unknown',
        count: item._count.id
      })),
      topTags: topTags.map(tag => ({
        id: tag.id,
        name: tag.name,
        color: tag.color,
        count: tag._count.bookmarks
      })),
      timeline: {
        recentActivity: Object.entries(bookmarksByDate)
          .map(([date, count]) => ({ date, count }))
          .sort((a, b) => a.date.localeCompare(b.date)),
        dateRange: {
          oldest: oldestBookmark?.createdAt || null,
          newest: newestBookmark?.createdAt || null
        }
      },
      health: {
        brokenLinksPercentage: totalBookmarks > 0 ? ((brokenBookmarks / totalBookmarks) * 100).toFixed(2) : '0',
        readPercentage: activeBookmarks > 0 ? ((readBookmarks / activeBookmarks) * 100).toFixed(2) : '0',
        avgTagsPerBookmark: totalBookmarks > 0 ? (await prisma.bookmarkTag.count() / totalBookmarks).toFixed(2) : '0'
      }
    }

    return NextResponse.json(stats)

  } catch (error) {
    console.error('Error fetching stats:', error)
    return NextResponse.json(
      { error: 'Failed to fetch statistics' },
      { status: 500 }
    )
  }
}