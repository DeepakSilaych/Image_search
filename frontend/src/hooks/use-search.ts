"use client";

import { useState, useCallback } from "react";
import { api, SearchResponse } from "@/lib/api";

export function useSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string, limit = 50) => {
    if (!query.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.search.query(query, limit);
      setResults(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, loading, error, search, clear };
}
