"use client";

import { useState, useCallback, useEffect } from "react";
import { api, StatsData } from "@/lib/api";

export function useStats() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await api.stats.get();
      setStats(data);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { stats, loading, refresh };
}
