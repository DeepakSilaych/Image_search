"use client";

import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { ImageGrid } from "@/components/image-grid";
import { UploadZone } from "@/components/upload-zone";
import { FolderBrowser } from "@/components/folder-browser";
import { useImages } from "@/hooks/use-images";
import { useStats } from "@/hooks/use-stats";
import {
  ChevronLeft, ChevronRight, FolderOpen, Loader2,
  Upload, HardDrive, RefreshCw, LayoutGrid, Folder,
} from "lucide-react";
import { api } from "@/lib/api";
import { FolderPicker } from "@/components/folder-picker";

type Tab = "folders" | "all" | "upload" | "scan";

export default function GalleryPage() {
  const { images, total, loading, page, load } = useImages(60);
  const { stats, refresh: refreshStats } = useStats();
  const [tab, setTab] = useState<Tab>("folders");

  const [scanDir, setScanDir] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [showPicker, setShowPicker] = useState(false);

  const gridImages = images.map((img) => ({
    id: img.id,
    caption: img.caption,
    scene_type: img.scene_type,
    faces: img.faces.map((f) => f.person_name).filter(Boolean) as string[],
  }));

  const totalPages = Math.ceil(total / 60);

  const handleScan = async () => {
    if (!scanDir.trim()) return;
    setScanning(true);
    setScanResult(null);
    try {
      const result = await api.images.scan(scanDir);
      setScanResult(`Discovered ${result.registered} new images (${result.skipped} already known)`);
      load(0);
      refreshStats();
    } catch (e: any) {
      setScanResult(`Error: ${e.message}`);
    } finally {
      setScanning(false);
    }
  };

  const pending = stats?.images.pending ?? 0;
  const processing = stats?.images.processing ?? 0;

  const tabs: { key: Tab; icon: typeof Folder; label: string }[] = [
    { key: "folders", icon: Folder, label: "Folders" },
    { key: "all", icon: LayoutGrid, label: "All" },
    { key: "upload", icon: Upload, label: "Upload" },
    { key: "scan", icon: HardDrive, label: "Scan" },
  ];

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Gallery</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-sm text-white/40">{stats?.images.total ?? total} photos</span>
              {(pending > 0 || processing > 0) && (
                <span className="flex items-center gap-1.5 text-xs text-amber-400">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  {processing > 0 ? `Processing ${processing}` : ""}{pending > 0 ? ` (${pending} queued)` : ""}
                </span>
              )}
              {stats?.worker_running && (
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-[10px] text-emerald-400">worker active</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1 glass rounded-lg p-0.5">
            {tabs.map(({ key, icon: Icon, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  tab === key ? "bg-accent text-white" : "text-white/50 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>

        {tab === "folders" && <FolderBrowser />}

        {tab === "upload" && (
          <div className="mb-8">
            <UploadZone onComplete={() => { load(0); refreshStats(); }} />
          </div>
        )}

        {tab === "scan" && (
          <div className="mb-8 space-y-4">
            <div className="glass rounded-xl p-5 space-y-4">
              <p className="text-sm text-white/50">Scan a directory to discover images. They will be queued for AI processing in the background.</p>
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={scanDir}
                    onChange={(e) => setScanDir(e.target.value)}
                    placeholder="e.g. /Users/you or ~/Pictures"
                    className="w-full px-3 py-2 pr-10 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-accent/50"
                    onKeyDown={(e) => e.key === "Enter" && handleScan()}
                  />
                  <button
                    onClick={() => setShowPicker((v) => !v)}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-md hover:bg-white/10 text-white/30 hover:text-white transition-colors"
                    title="Browse folders"
                  >
                    <FolderOpen className="w-4 h-4" />
                  </button>
                </div>
                <button
                  onClick={handleScan}
                  disabled={scanning || !scanDir.trim()}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
                >
                  {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <HardDrive className="w-4 h-4" />}
                  Scan
                </button>
              </div>
              {showPicker && (
                <FolderPicker
                  initialPath={scanDir || "/"}
                  onSelect={(path) => { setScanDir(path); setShowPicker(false); }}
                  onClose={() => setShowPicker(false)}
                />
              )}
              {scanResult && (
                <div className="px-4 py-2 rounded-lg bg-white/5 text-sm text-white/70">{scanResult}</div>
              )}
            </div>
          </div>
        )}

        {tab === "all" && (
          <>
            {loading ? (
              <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-white/30" /></div>
            ) : (
              <ImageGrid images={gridImages} />
            )}

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <button
                  onClick={() => load(page - 1)}
                  disabled={page === 0}
                  className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-white/50">Page {page + 1} of {totalPages}</span>
                <button
                  onClick={() => load(page + 1)}
                  disabled={page >= totalPages - 1}
                  className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-30 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
