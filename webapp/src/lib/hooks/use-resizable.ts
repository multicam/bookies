import { useState, useCallback, useRef, useEffect } from 'react'

interface UseResizableOptions {
  initialWidth?: number
  minWidth?: number
  maxWidth?: number
  storageKey?: string
}

export function useResizable({
  initialWidth = 256,
  minWidth = 200,
  maxWidth = 600,
  storageKey
}: UseResizableOptions = {}) {
  const [width, setWidth] = useState(() => {
    if (typeof window !== 'undefined' && storageKey) {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        const parsedWidth = parseInt(stored, 10)
        return Math.max(minWidth, Math.min(maxWidth, parsedWidth))
      }
    }
    return initialWidth
  })

  const [isResizing, setIsResizing] = useState(false)
  const startXRef = useRef<number>(0)
  const startWidthRef = useRef<number>(0)

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    startXRef.current = e.clientX
    startWidthRef.current = width

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [width])

  const stopResize = useCallback(() => {
    setIsResizing(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [])

  const resize = useCallback((e: MouseEvent) => {
    if (!isResizing) return

    const deltaX = e.clientX - startXRef.current
    const newWidth = startWidthRef.current + deltaX
    const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth))

    setWidth(constrainedWidth)

    if (storageKey) {
      localStorage.setItem(storageKey, constrainedWidth.toString())
    }
  }, [isResizing, minWidth, maxWidth, storageKey])

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', resize)
      document.addEventListener('mouseup', stopResize)

      return () => {
        document.removeEventListener('mousemove', resize)
        document.removeEventListener('mouseup', stopResize)
      }
    }
  }, [isResizing, resize, stopResize])

  return {
    width,
    isResizing,
    startResize
  }
}