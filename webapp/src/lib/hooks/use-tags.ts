'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { TagWithStats } from '@/lib/types'

const API_BASE = '/api'

export function useTags(search?: string, includeStats = false) {
  return useQuery({
    queryKey: ['tags', search, includeStats],
    queryFn: async () => {
      const searchParams = new URLSearchParams()

      if (search) searchParams.set('search', search)
      if (includeStats) searchParams.set('stats', 'true')

      const response = await fetch(`${API_BASE}/tags?${searchParams}`)
      if (!response.ok) throw new Error('Failed to fetch tags')

      return response.json() as Promise<TagWithStats[]>
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}

export function useCreateTag() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: { name: string; color?: string }) => {
      const response = await fetch(`${API_BASE}/tags`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create tag')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
    },
  })
}