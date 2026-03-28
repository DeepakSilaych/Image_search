"use client";

import { Sidebar } from "@/components/sidebar";
import { SearchBar } from "@/components/search-bar";
import { ImageGrid } from "@/components/image-grid";
import { useSearch } from "@/hooks/use-search";
import { Sparkles } from "lucide-react";

export default function SearchPage() {
  const { results, loading, error, search } = useSearch();

  const gridImages = results?.hits.map((h) => ({
    id: h.image_id,
    caption: h.caption,
    scene_type: h.scene_type,
    faces: h.faces,
    score: h.score,
    match_reasons: h.match_reasons,
  })) || [];

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen">
        <div className="flex flex-col items-center pt-20 px-6">
          {!results && (
            <div className="text-center mb-8">
              <Sparkles className="w-10 h-10 text-accent mx-auto mb-4" />
              <h1 className="text-3xl font-bold tracking-tight">Search Your Memories</h1>
              <p className="text-sm text-white/40 mt-2 max-w-md">
                Describe what you&apos;re looking for in natural language. Try people, places, objects, emotions, or time.
              </p>
            </div>
          )}

          <SearchBar onSearch={search} loading={loading} />

          {results?.parsed_query && (
            <div className="flex flex-wrap gap-2 mt-4 max-w-2xl">
              {(results.parsed_query as any).persons?.map((p: string) => (
                <span key={p} className="px-2 py-1 rounded-full bg-accent/10 text-xs text-accent">person: {p}</span>
              ))}
              {(results.parsed_query as any).scenes?.map((s: string) => (
                <span key={s} className="px-2 py-1 rounded-full bg-emerald-500/10 text-xs text-emerald-400">scene: {s}</span>
              ))}
              {(results.parsed_query as any).emotions?.map((e: string) => (
                <span key={e} className="px-2 py-1 rounded-full bg-amber-500/10 text-xs text-amber-400">mood: {e}</span>
              ))}
              {(results.parsed_query as any).year && (
                <span className="px-2 py-1 rounded-full bg-cyan-500/10 text-xs text-cyan-400">year: {(results.parsed_query as any).year}</span>
              )}
              {(results.parsed_query as any).is_group && (
                <span className="px-2 py-1 rounded-full bg-purple-500/10 text-xs text-purple-400">group photo</span>
              )}
            </div>
          )}

          {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

          {results && (
            <p className="text-xs text-white/30 mt-4 mb-2">
              {results.total} result{results.total !== 1 ? "s" : ""}
            </p>
          )}
        </div>

        <div className="px-6 pb-8">
          <ImageGrid images={gridImages} />
        </div>
      </main>
    </div>
  );
}
