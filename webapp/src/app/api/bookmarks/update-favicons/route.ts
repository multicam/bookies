import { NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'
import { FaviconService } from '@/lib/favicon-service'

const prisma = new PrismaClient()

export async function POST() {
  try {
    // Get bookmarks without favicons
    const bookmarks = await prisma.bookmark.findMany({
      where: {
        status: 'active',
        faviconUrl: null,
        domain: {
          not: null
        }
      },
      select: {
        id: true,
        domain: true,
        url: true
      },
      take: 100 // Process in batches to avoid overwhelming the system
    })

    if (bookmarks.length === 0) {
      return NextResponse.json({
        message: 'No bookmarks need favicon updates',
        updated: 0
      })
    }

    let updated = 0
    const updates: Array<Promise<any>> = []

    // Process each bookmark
    for (const bookmark of bookmarks) {
      if (bookmark.domain) {
        const faviconUrl = FaviconService.getFaviconUrl(bookmark.domain)

        if (faviconUrl) {
          const updatePromise = prisma.bookmark.update({
            where: { id: bookmark.id },
            data: { faviconUrl }
          })

          updates.push(updatePromise)
          updated++
        }
      }
    }

    // Execute all updates in parallel
    if (updates.length > 0) {
      await Promise.all(updates)
    }

    return NextResponse.json({
      message: `Updated ${updated} bookmarks with favicons`,
      updated,
      total: bookmarks.length
    })

  } catch (error) {
    console.error('Error updating favicons:', error)
    return NextResponse.json(
      { error: 'Failed to update favicons' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    // Get statistics about favicon coverage
    const totalBookmarks = await prisma.bookmark.count({
      where: { status: 'active' }
    })

    const withFavicons = await prisma.bookmark.count({
      where: {
        status: 'active',
        faviconUrl: { not: null }
      }
    })

    const withoutFavicons = await prisma.bookmark.count({
      where: {
        status: 'active',
        faviconUrl: null,
        domain: { not: null }
      }
    })

    return NextResponse.json({
      total: totalBookmarks,
      withFavicons,
      withoutFavicons,
      coverage: totalBookmarks > 0 ? Math.round((withFavicons / totalBookmarks) * 100) : 0
    })

  } catch (error) {
    console.error('Error getting favicon stats:', error)
    return NextResponse.json(
      { error: 'Failed to get favicon statistics' },
      { status: 500 }
    )
  }
}