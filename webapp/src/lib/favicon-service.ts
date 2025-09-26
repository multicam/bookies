export class FaviconService {
  private static cache = new Map<string, string | null>()

  // Common favicon service URLs
  private static services = [
    // Google's favicon service - most reliable
    (domain: string) => `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
    // DuckDuckGo's favicon service - good fallback
    (domain: string) => `https://icons.duckduckgo.com/ip3/${domain}.ico`,
    // Yandex favicon service
    (domain: string) => `https://favicon.yandex.net/favicon/${domain}`,
  ]

  /**
   * Get favicon URL for a domain with fallback services
   */
  static getFaviconUrl(domain: string): string {
    if (!domain) return ''

    // Use Google's service as primary (most reliable)
    return this.services[0](domain)
  }

  /**
   * Extract domain from URL
   */
  static extractDomain(url: string): string | null {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.replace('www.', '')
    } catch {
      return null
    }
  }

  /**
   * Get favicon URL from full URL
   */
  static getFaviconFromUrl(url: string): string | null {
    const domain = this.extractDomain(url)
    return domain ? this.getFaviconUrl(domain) : null
  }

  /**
   * Batch process multiple URLs to get their favicons
   */
  static getFaviconsFromUrls(urls: string[]): Map<string, string | null> {
    const result = new Map<string, string | null>()

    urls.forEach(url => {
      const favicon = this.getFaviconFromUrl(url)
      result.set(url, favicon)
    })

    return result
  }

  /**
   * Test if a favicon URL is working (for use in components)
   */
  static async testFavicon(faviconUrl: string): Promise<boolean> {
    if (this.cache.has(faviconUrl)) {
      return this.cache.get(faviconUrl) !== null
    }

    try {
      const response = await fetch(faviconUrl, {
        method: 'HEAD',
        mode: 'no-cors',  // Handle CORS issues
        cache: 'force-cache'  // Use browser cache
      })
      const isValid = response.ok || response.type === 'opaque'
      this.cache.set(faviconUrl, isValid ? faviconUrl : null)
      return isValid
    } catch {
      this.cache.set(faviconUrl, null)
      return false
    }
  }
}

/**
 * Hook for components to get favicon URL from domain or URL
 */
export function useFavicon(urlOrDomain: string): string | null {
  if (!urlOrDomain) return null

  // Check if it's a URL or just a domain
  if (urlOrDomain.startsWith('http')) {
    return FaviconService.getFaviconFromUrl(urlOrDomain)
  } else {
    return FaviconService.getFaviconUrl(urlOrDomain)
  }
}