"use client";

import { useState, FormEvent } from "react";
import { Search, X, Loader2 } from "lucide-react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export function SearchBar({ onSearch, loading, placeholder }: SearchBarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl">
      <div className="relative flex items-center">
        <Search className="absolute left-4 w-4 h-4 text-white/40" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder || "Search your memories..."}
          className="w-full pl-11 pr-20 py-3 rounded-xl glass text-sm text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all"
        />
        <div className="absolute right-2 flex items-center gap-1">
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(""); onSearch(""); }}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X className="w-3.5 h-3.5 text-white/40" />
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Search"}
          </button>
        </div>
      </div>
    </form>
  );
}
