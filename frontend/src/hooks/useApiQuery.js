import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Tiny stale-while-revalidate query cache (no external dependency).
 * - Returns cached data instantly on revisit so navigation feels instant.
 * - Deduplicates concurrent/StrictMode-double calls for the same key.
 * - Revalidates in the background when data is older than `staleTime`.
 */
const cache = new Map();     // key -> { data, ts }
const inflight = new Map();  // key -> Promise

export function invalidate(prefix = "") {
  for (const k of [...cache.keys()]) {
    if (k.startsWith(prefix)) cache.delete(k);
  }
}

export function clearApiCache() {
  cache.clear();
  inflight.clear();
}

export function useApiQuery(key, fetcher, { staleTime = 30000, enabled = true } = {}) {
  const [data, setData] = useState(() => cache.get(key)?.data);
  const [loading, setLoading] = useState(() => enabled && !cache.has(key));
  const [error, setError] = useState(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const run = useCallback(
    async (force = false) => {
      const entry = cache.get(key);
      if (entry) setData(entry.data);
      const fresh = entry && Date.now() - entry.ts < staleTime;
      if (fresh && !force) {
        setLoading(false);
        return entry.data;
      }
      let p = inflight.get(key);
      if (!p) {
        p = Promise.resolve()
          .then(() => fetcherRef.current())
          .then((d) => {
            cache.set(key, { data: d, ts: Date.now() });
            inflight.delete(key);
            return d;
          })
          .catch((e) => {
            inflight.delete(key);
            throw e;
          });
        inflight.set(key, p);
      }
      if (!entry) setLoading(true);
      try {
        const d = await p;
        setData(d);
        setError(null);
        return d;
      } catch (e) {
        setError(e);
      } finally {
        setLoading(false);
      }
    },
    [key, staleTime]
  );

  useEffect(() => {
    if (enabled) run();
  }, [key, enabled, run]);

  return { data, loading, error, refetch: () => run(true) };
}

export function useDebounced(value, delay = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return v;
}
