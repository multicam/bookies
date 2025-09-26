import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const search = searchParams.get('search')
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100)
    const includeStats = searchParams.get('stats') === 'true'

    // Build where clause for search
    const where: any = {}
    if (search) {
      where.name = {
        contains: search,
        mode: 'insensitive'
      }
    }

    if (includeStats) {
      // Get tags with bookmark counts
      const tags = await prisma.tag.findMany({
        where,
        orderBy: [
          { usageCount: 'desc' },
          { name: 'asc' }
        ],
        take: limit,
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
        }
      })

      return NextResponse.json(tags)
    } else {
      // Simple tag list
      const tags = await prisma.tag.findMany({
        where,
        orderBy: [
          { usageCount: 'desc' },
          { name: 'asc' }
        ],
        take: limit
      })

      return NextResponse.json(tags)
    }

  } catch (error) {
    console.error('Error fetching tags:', error)
    return NextResponse.json(
      { error: 'Failed to fetch tags' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, color } = body

    if (!name || typeof name !== 'string') {
      return NextResponse.json(
        { error: 'Tag name is required' },
        { status: 400 }
      )
    }

    const trimmedName = name.trim()
    if (!trimmedName) {
      return NextResponse.json(
        { error: 'Tag name cannot be empty' },
        { status: 400 }
      )
    }

    // Create or get existing tag
    const tag = await prisma.tag.upsert({
      where: { name: trimmedName },
      update: {
        color: color || undefined
      },
      create: {
        name: trimmedName,
        color: color || '#6B7280',
        usageCount: 0
      }
    })

    return NextResponse.json(tag, { status: 201 })

  } catch (error) {
    console.error('Error creating tag:', error)
    return NextResponse.json(
      { error: 'Failed to create tag' },
      { status: 500 }
    )
  }
}