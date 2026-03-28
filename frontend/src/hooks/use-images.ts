"use client";

import { useState, useCallback, useEffect } from "react";
import { api, ImageData } from "@/lib/api";

export function useImages(initialLimit = 50) {
  const [images, setImages] = useState<ImageData[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);

  const load = useCallback(async (p = 0) => {
    setLoading(true);
    try {
      const data = await api.images.list(p * initialLimit, initialLimit);
      setImages(data.items);
      setTotal(data.total);
      setPage(p);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [initialLimit]);

  useEffect(() => { load(0); }, [load]);

  return { images, total, loading, page, load, setPage };
}
