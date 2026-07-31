import { useEffect, useState } from 'react'

/** Loads data from a mock.ts getter on mount. Every page uses this the same way a real
 * `api.get<T>(...)` call would be used, so swapping the fetcher later needs no page
 * changes - see mock.ts's header comment. */
export function useMock<T>(fetcher: () => Promise<T>, deps: unknown[] = []): { data: T | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetcher().then((result) => {
      if (!cancelled) {
        setData(result)
        setLoading(false)
      }
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading }
}
