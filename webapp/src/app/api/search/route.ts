import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const query = searchParams.get('q')
    const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 50)

    if (!query || query.trim().length < 2) {
      return NextResponse.json(
        { error: 'Search query must be at least 2 characters' },
        { status: 400 }
      )
    }

    const searchTerm = query.trim()

    // Perform full-text search across bookmarks
    const bookmarks = await prisma.bookmark.findMany({
      where: {
        status: 'active',
        OR: [
          {
            title: {
              contains: searchTerm
            }
          },
          {
            description: {
              contains: searchTerm
            }
          },
          {
            url: {
              contains: searchTerm
            }
          },
          {
            domain: {
              contains: searchTerm
            }
          },
          {
            tags: {
              some: {
                tag: {
                  name: {
                    contains: searchTerm
                  }
                }
              }
            }
          }
        ]
      },
      include: {
        tags: {
          include: {
            tag: true
          }
        }
      },
      orderBy: [
        // Prioritize exact title matches
        {
          title: 'asc'
        },
        {
          createdAt: 'desc'
        }
      ],
      take: limit
    })

    // Also search for matching tags
    const tags = await prisma.tag.findMany({
      where: {
        name: {
          contains: searchTerm
        }
      },
      orderBy: {
        usageCount: 'desc'
      },
      take: 10
    })

    // Search for domains
    const domains = await prisma.bookmark.groupBy({
      by: ['domain'],
      where: {
        status: 'active',
        domain: {
          contains: searchTerm
        }
      },
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

    const response = {
      query: searchTerm,
      results: {
        bookmarks: bookmarks,
        tags: tags,
        domains: domains.map(d => ({
          domain: d.domain,
          count: d._count?.id || 0
        }))
      },
      totalResults: bookmarks.length
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('Error performing search:', error)
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      query,
      filters = {},
      sort = { field: 'createdAt', order: 'desc' },
      page = 1,
      limit = 20
    } = body

    const skip = (page - 1) * Math.min(limit, 50)
    const take = Math.min(limit, 50)

    // Build advanced search query
    const where: any = {
      status: filters.status || 'active'
    }

    // Apply filters
    if (filters.favorite !== undefined) {
      where.favorite = filters.favorite
    }

    if (filters.readStatus !== undefined) {
      where.readStatus = filters.readStatus
    }

    if (filters.domains && Array.isArray(filters.domains) && filters.domains.length > 0) {
      where.domain = {
        in: filters.domains
      }
    }

    if (filters.tags && Array.isArray(filters.tags) && filters.tags.length > 0) {
      where.tags = {
        some: {
          tag: {
            name: {
              in: filters.tags
            }
          }
        }
      }
    }

    if (filters.dateRange) {
      where.createdAt = {}
      if (filters.dateRange.from) {
        where.createdAt.gte = new Date(filters.dateRange.from)
      }
      if (filters.dateRange.to) {
        where.createdAt.lte = new Date(filters.dateRange.to)
      }
    }

    // Apply text search
    if (query && query.trim()) {
      const searchTerm = query.trim()
      where.OR = [
        { title: { contains: searchTerm } },
        { description: { contains: searchTerm } },
        { url: { contains: searchTerm } },
        {
          tags: {
            some: {
              tag: {
                name: { contains: searchTerm }
              }
            }
          }
        }
      ]
    }

    // Build sort
    const orderBy: any = {}
    orderBy[sort.field] = sort.order

    // Get total count
    const total = await prisma.bookmark.count({ where })

    // Get bookmarks
    const bookmarks = await prisma.bookmark.findMany({
      where,
      orderBy,
      skip,
      take,
      include: {
        tags: {
          include: {
            tag: true
          }
        },
        collections: {
          include: {
            collection: true
          }
        }
      }
    })

    const response = {
      items: bookmarks,
      total,
      page,
      limit: take,
      hasMore: skip + bookmarks.length < total,
      query,
      filters,
      sort
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('Error performing advanced search:', error)
    return NextResponse.json(
      { error: 'Advanced search failed' },
      { status: 500 }
    )
  }
}