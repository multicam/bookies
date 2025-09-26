import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import type { BookmarkFilters, SortConfig, PaginatedResponse } from '@/lib/types'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Parse query parameters
    const page = parseInt(searchParams.get('page') || '1')
    const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 100) // Max 100 items
    const query = searchParams.get('query')
    const tags = searchParams.get('tags')?.split(',').filter(Boolean) || []
    const domains = searchParams.get('domains')?.split(',').filter(Boolean) || []
    const status = searchParams.get('status') as 'active' | 'archived' | 'broken' | undefined
    const favorite = searchParams.get('favorite') === 'true' ? true : undefined
    const readStatus = searchParams.get('readStatus') === 'true' ? true : undefined

    // Sort parameters
    const sortField = (searchParams.get('sortField') as 'createdAt' | 'updatedAt' | 'title' | 'domain') || 'createdAt'
    const sortOrder = (searchParams.get('sortOrder') as 'asc' | 'desc') || 'desc'

    const skip = (page - 1) * limit

    // Build where clause
    const where: any = {
      status: status || 'active'
    }

    if (favorite !== undefined) {
      where.favorite = favorite
    }

    if (readStatus !== undefined) {
      where.readStatus = readStatus
    }

    if (domains.length > 0) {
      where.domain = {
        in: domains
      }
    }

    if (tags.length > 0) {
      where.tags = {
        some: {
          tag: {
            name: {
              in: tags
            }
          }
        }
      }
    }

    // Handle full-text search query
    if (query) {
      where.OR = [
        { title: { contains: query } },
        { description: { contains: query } },
        { url: { contains: query } },
        {
          tags: {
            some: {
              tag: {
                name: { contains: query }
              }
            }
          }
        }
      ]
    }

    // Build sort clause
    const orderBy: any = {}
    orderBy[sortField] = sortOrder

    // Get total count for pagination
    const total = await prisma.bookmark.count({ where })

    // Fetch bookmarks with relations
    const bookmarks = await prisma.bookmark.findMany({
      where,
      orderBy,
      skip,
      take: limit,
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

    const response: PaginatedResponse<typeof bookmarks[0]> = {
      items: bookmarks,
      total,
      page,
      limit,
      hasMore: skip + bookmarks.length < total
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('Error fetching bookmarks:', error)
    return NextResponse.json(
      { error: 'Failed to fetch bookmarks' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, title, description, tags, collections, favorite, readStatus } = body

    if (!url) {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      )
    }

    // Generate URL hash for deduplication (similar to Python implementation)
    const urlHash = Buffer.from(url.toLowerCase().trim()).toString('base64')

    // Extract domain
    let domain = ''
    try {
      domain = new URL(url).hostname.toLowerCase()
    } catch (e) {
      // Invalid URL, use empty domain
    }

    // Create bookmark
    const bookmark = await prisma.bookmark.create({
      data: {
        url,
        title: title || '',
        description: description || '',
        domain,
        urlHash,
        source: 'manual',
        favorite: favorite || false,
        readStatus: readStatus || false,
      },
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

    // Add tags if provided
    if (tags && Array.isArray(tags) && tags.length > 0) {
      for (const tagName of tags) {
        // Get or create tag
        const tag = await prisma.tag.upsert({
          where: { name: tagName },
          update: { usageCount: { increment: 1 } },
          create: { name: tagName, usageCount: 1 }
        })

        // Link bookmark to tag
        await prisma.bookmarkTag.create({
          data: {
            bookmarkId: bookmark.id,
            tagId: tag.id
          }
        })
      }

      // Refetch bookmark with tags
      const bookmarkWithTags = await prisma.bookmark.findUnique({
        where: { id: bookmark.id },
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

      return NextResponse.json(bookmarkWithTags, { status: 201 })
    }

    return NextResponse.json(bookmark, { status: 201 })

  } catch (error) {
    console.error('Error creating bookmark:', error)

    // Handle unique constraint violation (duplicate URL)
    if (error instanceof Error && error.message.includes('Unique constraint')) {
      return NextResponse.json(
        { error: 'A bookmark with this URL already exists' },
        { status: 409 }
      )
    }

    return NextResponse.json(
      { error: 'Failed to create bookmark' },
      { status: 500 }
    )
  }
}