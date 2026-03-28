"use client";

import { useState, useEffect, useCallback } from "react";
import { Folder, ChevronRight, ArrowUp, Check, X } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  onSelect: (path: string) => void;
  onClose: () => void;
  initialPath?: string;
}

export function FolderPicker({ onSelect, onClose, initialPath = "/" }: Props) {
  const [current, setCurrent] = useState(initialPath);
  const [parent, setParent] = useState("/");
  const [dirs, setDirs] = useState<{ name: string; path: string }[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (path: string) => {
    setLoading(true);
    try {
      const data = await api.images.browse(path);
      setCurrent(data.current);
      setParent(data.parent);
      setDirs(data.dirs);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(initialPath); }, [initialPath, load]);

  return (
    <div className="glass rounded-xl border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => load(parent)}
            disabled={current === parent}
            className="p-1 rounded hover:bg-white/5 disabled:opacity-20 transition-colors shrink-0"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
          <span className="text-xs text-white/40 truncate">{current}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            onClick={() => onSelect(current)}
            className="flex items-center gap-1 px-3 py-1 rounded-md bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors"
          >
            <Check className="w-3 h-3" />
            Select
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-white/5 text-white/40 hover:text-white transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="max-h-64 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="w-4 h-4 border-2 border-white/10 border-t-accent rounded-full animate-spin" />
          </div>
        ) : dirs.length === 0 ? (
          <p className="text-xs text-white/20 text-center py-6">No subdirectories</p>
        ) : (
          dirs.map((d) => (
            <button
              key={d.path}
              onClick={() => load(d.path)}
              onDoubleClick={() => onSelect(d.path)}
              className="w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-white/[0.04] transition-colors group"
            >
              <Folder className="w-4 h-4 text-accent/50 group-hover:text-accent shrink-0 transition-colors" />
              <span className="text-sm truncate">{d.name}</span>
              <ChevronRight className="w-3 h-3 text-white/10 ml-auto shrink-0" />
            </button>
          ))
        )}
      </div>
    </div>
  );
}
