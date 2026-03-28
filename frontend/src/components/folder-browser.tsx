"use client";

import { useState, useEffect, useCallback } from "react";
import { Folder, ChevronRight, Image as ImageIcon, ArrowLeft, Home } from "lucide-react";
import { api, FolderData, ImageData } from "@/lib/api";
import { ImageGrid } from "./image-grid";

export function FolderBrowser() {
  const [pathStack, setPathStack] = useState<string[]>([]);
  const [folders, setFolders] = useState<FolderData[]>([]);
  const [images, setImages] = useState<ImageData[]>([]);
  const [imageTotal, setImageTotal] = useState(0);
  const [rootPath, setRootPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const currentPath = pathStack.length > 0 ? pathStack[pathStack.length - 1] : undefined;

  const loadFolder = useCallback(async (root?: string) => {
    setLoading(true);
    try {
      const treeData = await api.images.folders(root);
      setFolders(treeData.folders);
      setRootPath(treeData.root);

      const loadPath = root || treeData.root;
      if (treeData.direct_images > 0) {
        const imageData = await api.images.folderImages(loadPath);
        setImages(imageData.items);
        setImageTotal(imageData.total);
      } else {
        setImages([]);
        setImageTotal(0);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadFolder(currentPath); }, [currentPath, loadFolder]);

  const openFolder = (path: string) => setPathStack((prev) => [...prev, path]);
  const goBack = () => setPathStack((prev) => prev.slice(0, -1));
  const goToRoot = () => setPathStack([]);
  const goToIndex = (idx: number) => setPathStack((prev) => prev.slice(0, idx + 1));

  const displayRoot = rootPath ? rootPath.split("/").filter(Boolean).pop() || rootPath : "Root";

  const breadcrumbs = pathStack.map((p) => {
    const name = p.split("/").filter(Boolean).pop() || p;
    return { path: p, name };
  });

  const gridImages = images.map((img) => ({
    id: img.id,
    caption: img.caption,
    scene_type: img.scene_type,
    faces: img.faces.map((f) => f.person_name).filter(Boolean) as string[],
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm overflow-x-auto pb-1">
        <button
          onClick={goToRoot}
          className={`shrink-0 flex items-center gap-1 px-2 py-1 rounded-md transition-colors ${
            !currentPath ? "text-accent" : "text-white/50 hover:text-white hover:bg-white/5"
          }`}
        >
          <Home className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">{displayRoot}</span>
        </button>

        {breadcrumbs.map((crumb, i) => (
          <div key={crumb.path} className="flex items-center gap-1 shrink-0">
            <ChevronRight className="w-3 h-3 text-white/20" />
            <button
              onClick={() => goToIndex(i)}
              className={`px-2 py-1 rounded-md transition-colors truncate max-w-[150px] ${
                i === breadcrumbs.length - 1
                  ? "text-accent"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              {crumb.name}
            </button>
          </div>
        ))}

        {pathStack.length > 0 && (
          <button
            onClick={goBack}
            className="ml-auto shrink-0 flex items-center gap-1 px-2 py-1 rounded-md text-white/40 hover:text-white hover:bg-white/5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-5 h-5 border-2 border-white/10 border-t-accent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {folders.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
              {folders.map((f) => (
                <button
                  key={f.path}
                  onClick={() => openFolder(f.path)}
                  className="glass rounded-xl p-4 text-left hover:bg-white/[0.06] hover:ring-1 hover:ring-accent/30 transition-all group"
                >
                  <Folder className="w-8 h-8 text-accent/60 group-hover:text-accent mb-2 transition-colors" />
                  <p className="text-sm font-medium truncate">{f.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="flex items-center gap-1 text-[10px] text-white/30">
                      <ImageIcon className="w-3 h-3" />{f.total_count}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {images.length > 0 && (
            <div className="pt-2">
              {folders.length > 0 && (
                <p className="text-xs text-white/30 mb-3">{imageTotal} images in this folder</p>
              )}
              <ImageGrid images={gridImages} />
            </div>
          )}

          {folders.length === 0 && images.length === 0 && (
            <div className="text-center py-16 text-white/25">
              <Folder className="w-10 h-10 mx-auto mb-3" />
              <p>No indexed images here</p>
              <p className="text-sm mt-1">Scan a directory first from the Scan tab</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
