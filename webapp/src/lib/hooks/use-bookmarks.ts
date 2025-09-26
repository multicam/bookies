'use client'

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { BookmarkWithTags, BookmarkFilters, SortConfig, PaginatedResponse } from '@/lib/types'

// API base URL
const API_BASE = '/api'

// Fetch bookmarks with infinite scroll support
export function useInfiniteBookmarks(filters: BookmarkFilters = {}, sort: SortConfig = { field: 'createdAt', order: 'desc' }) {
  return useInfiniteQuery({
    queryKey: ['bookmarks', 'infinite', filters, sort],
    queryFn: async ({ pageParam = 1 }) => {
      const searchParams = new URLSearchParams({
        page: pageParam.toString(),
        limit: '20',
        sortField: sort.field,
        sortOrder: sort.order,
      })

      if (filters.query) searchParams.set('query', filters.query)
      if (filters.tags?.length) searchParams.set('tags', filters.tags.join(','))
      if (filters.domains?.length) searchParams.set('domains', filters.domains.join(','))
      if (filters.status) searchParams.set('status', filters.status)
      if (filters.favorite !== undefined) searchParams.set('favorite', filters.favorite.toString())
      if (filters.readStatus !== undefined) searchParams.set('readStatus', filters.readStatus.toString())

      const response = await fetch(`${API_BASE}/bookmarks?${searchParams}`)
      if (!response.ok) throw new Error('Failed to fetch bookmarks')

      return response.json() as Promise<PaginatedResponse<BookmarkWithTags>>
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.page + 1 : undefined,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch single bookmark
export function useBookmark(id: number) {
  return useQuery({
    queryKey: ['bookmarks', id],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/bookmarks/${id}`)
      if (!response.ok) {
        if (response.status === 404) throw new Error('Bookmark not found')
        throw new Error('Failed to fetch bookmark')
      }
      return response.json() as Promise<BookmarkWithTags>
    },
    enabled: !!id,
  })
}

// Create bookmark mutation
export function useCreateBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      url: string
      title?: string
      description?: string
      tags?: string[]
      favorite?: boolean
      readStatus?: boolean
    }) => {
      const response = await fetch(`${API_BASE}/bookmarks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create bookmark')
      }

      return response.json() as Promise<BookmarkWithTags>
    },
    onSuccess: () => {
      // Invalidate bookmark queries
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['tags'] })
    },
  })
}

// Update bookmark mutation
export function useUpdateBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...data }: {
      id: number
      title?: string
      description?: string
      tags?: string[]
      favorite?: boolean
      readStatus?: boolean
    }) => {
      const response = await fetch(`${API_BASE}/bookmarks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to update bookmark')
      }

      return response.json() as Promise<BookmarkWithTags>
    },
    onSuccess: (data) => {
      // Update specific bookmark in cache
      queryClient.setQueryData(['bookmarks', data.id], data)

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['bookmarks', 'infinite'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

// Delete bookmark mutation
export function useDeleteBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, hard = false }: { id: number; hard?: boolean }) => {
      const searchParams = hard ? '?hard=true' : ''
      const response = await fetch(`${API_BASE}/bookmarks/${id}${searchParams}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to delete bookmark')
      }

      return response.json()
    },
    onSuccess: () => {
      // Invalidate bookmark queries
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

// Toggle bookmark favorite
export function useToggleFavorite() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, favorite }: { id: number; favorite: boolean }) => {
      const response = await fetch(`${API_BASE}/bookmarks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ favorite }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to toggle favorite')
      }

      return response.json() as Promise<BookmarkWithTags>
    },
    onSuccess: (data) => {
      // Update bookmark in cache
      queryClient.setQueryData(['bookmarks', data.id], data)

      // Invalidate infinite queries
      queryClient.invalidateQueries({ queryKey: ['bookmarks', 'infinite'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

// Toggle bookmark read status
export function useToggleReadStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, readStatus }: { id: number; readStatus: boolean }) => {
      const response = await fetch(`${API_BASE}/bookmarks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ readStatus }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to toggle read status')
      }

      return response.json() as Promise<BookmarkWithTags>
    },
    onSuccess: (data) => {
      // Update bookmark in cache
      queryClient.setQueryData(['bookmarks', data.id], data)

      // Invalidate infinite queries
      queryClient.invalidateQueries({ queryKey: ['bookmarks', 'infinite'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

// Search bookmarks
export function useSearchBookmarks(query: string, enabled = true) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      if (!query.trim()) return { results: { bookmarks: [], tags: [], domains: [] }, totalResults: 0 }

      const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query.trim())}&limit=20`)
      if (!response.ok) throw new Error('Search failed')

      return response.json()
    },
    enabled: enabled && query.trim().length >= 2,
    staleTime: 1000 * 30, // 30 seconds
  })
}

// Advanced search
export function useAdvancedSearch() {
  return useMutation({
    mutationFn: async (searchData: {
      query?: string
      filters?: BookmarkFilters
      sort?: SortConfig
      page?: number
      limit?: number
    }) => {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(searchData),
      })

      if (!response.ok) throw new Error('Advanced search failed')

      return response.json() as Promise<PaginatedResponse<BookmarkWithTags>>
    },
  })
}