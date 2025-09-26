import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

interface RouteParams {
  params: Promise<{
    id: string
  }>
}

export async function GET(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    const resolvedParams = await params
    const id = parseInt(resolvedParams.id)

    if (isNaN(id)) {
      return NextResponse.json(
        { error: 'Invalid bookmark ID' },
        { status: 400 }
      )
    }

    const bookmark = await prisma.bookmark.findUnique({
      where: { id },
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

    if (!bookmark) {
      return NextResponse.json(
        { error: 'Bookmark not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(bookmark)

  } catch (error) {
    console.error('Error fetching bookmark:', error)
    return NextResponse.json(
      { error: 'Failed to fetch bookmark' },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    const resolvedParams = await params
    const id = parseInt(resolvedParams.id)
    const body = await request.json()

    if (isNaN(id)) {
      return NextResponse.json(
        { error: 'Invalid bookmark ID' },
        { status: 400 }
      )
    }

    const { title, description, favorite, readStatus, tags } = body

    // Check if bookmark exists
    const existingBookmark = await prisma.bookmark.findUnique({
      where: { id }
    })

    if (!existingBookmark) {
      return NextResponse.json(
        { error: 'Bookmark not found' },
        { status: 404 }
      )
    }

    // Update bookmark
    const updatedBookmark = await prisma.bookmark.update({
      where: { id },
      data: {
        title: title !== undefined ? title : existingBookmark.title,
        description: description !== undefined ? description : existingBookmark.description,
        favorite: favorite !== undefined ? favorite : existingBookmark.favorite,
        readStatus: readStatus !== undefined ? readStatus : existingBookmark.readStatus,
        updatedAt: new Date()
      }
    })

    // Handle tags update if provided
    if (tags && Array.isArray(tags)) {
      // Remove all existing tags
      await prisma.bookmarkTag.deleteMany({
        where: { bookmarkId: id }
      })

      // Add new tags
      for (const tagName of tags) {
        if (typeof tagName === 'string' && tagName.trim()) {
          // Get or create tag
          const tag = await prisma.tag.upsert({
            where: { name: tagName.trim() },
            update: { usageCount: { increment: 1 } },
            create: { name: tagName.trim(), usageCount: 1 }
          })

          // Link bookmark to tag
          await prisma.bookmarkTag.create({
            data: {
              bookmarkId: id,
              tagId: tag.id
            }
          })
        }
      }

      // Clean up unused tags (optional - you might want to keep them)
      await prisma.tag.deleteMany({
        where: {
          bookmarks: {
            none: {}
          }
        }
      })
    }

    // Fetch updated bookmark with relations
    const bookmarkWithRelations = await prisma.bookmark.findUnique({
      where: { id },
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

    return NextResponse.json(bookmarkWithRelations)

  } catch (error) {
    console.error('Error updating bookmark:', error)
    return NextResponse.json(
      { error: 'Failed to update bookmark' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    const resolvedParams = await params
    const id = parseInt(resolvedParams.id)

    if (isNaN(id)) {
      return NextResponse.json(
        { error: 'Invalid bookmark ID' },
        { status: 400 }
      )
    }

    // Check if bookmark exists
    const existingBookmark = await prisma.bookmark.findUnique({
      where: { id }
    })

    if (!existingBookmark) {
      return NextResponse.json(
        { error: 'Bookmark not found' },
        { status: 404 }
      )
    }

    // Soft delete - mark as archived instead of hard delete
    const softDelete = request.nextUrl.searchParams.get('hard') !== 'true'

    if (softDelete) {
      await prisma.bookmark.update({
        where: { id },
        data: {
          status: 'ARCHIVED',
          updatedAt: new Date()
        }
      })

      return NextResponse.json({ message: 'Bookmark archived successfully' })
    } else {
      // Hard delete - remove completely
      await prisma.bookmark.delete({
        where: { id }
      })

      return NextResponse.json({ message: 'Bookmark deleted successfully' })
    }

  } catch (error) {
    console.error('Error deleting bookmark:', error)
    return NextResponse.json(
      { error: 'Failed to delete bookmark' },
      { status: 500 }
    )
  }
}