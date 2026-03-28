"use client";

import { useState } from "react";
import { Heart, MapPin, Clock, Tag } from "lucide-react";
import { api } from "@/lib/api";
import { ImagePreview } from "./image-preview";

interface GridImage {
  id: string;
  caption?: string | null;
  scene_type?: string | null;
  faces?: string[];
  score?: number;
  match_reasons?: string[];
}

interface ImageGridProps {
  images: GridImage[];
}

export function ImageGrid({ images }: ImageGridProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (!images.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-white/30">
        <p className="text-lg">No images found</p>
        <p className="text-sm mt-1">Try a different search or index some photos</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-1.5">
        {images.map((img) => (
          <div
            key={img.id}
            onClick={() => setSelectedId(img.id)}
            className="group relative aspect-square rounded-lg overflow-hidden cursor-pointer bg-surface-100 hover:ring-1 hover:ring-accent/40 transition-all"
          >
            <img
              src={api.images.thumbnailUrl(img.id)}
              alt={img.caption || ""}
              loading="lazy"
              className="w-full h-full object-cover transition-transform group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {img.caption && (
                <p className="text-[10px] text-white/80 line-clamp-2">{img.caption}</p>
              )}
              <div className="flex items-center gap-1 mt-1 flex-wrap">
                {img.scene_type && (
                  <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/10 text-[9px] text-white/70">
                    <MapPin className="w-2.5 h-2.5" />{img.scene_type}
                  </span>
                )}
                {img.faces?.map((f) => (
                  <span key={f} className="px-1.5 py-0.5 rounded bg-accent/20 text-[9px] text-accent">
                    {f}
                  </span>
                ))}
                {img.score !== undefined && (
                  <span className="px-1.5 py-0.5 rounded bg-green-500/20 text-[9px] text-green-400">
                    {(img.score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedId && (
        <ImagePreview imageId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </>
  );
}
