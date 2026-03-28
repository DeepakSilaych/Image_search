"use client";

import { useState, useCallback, DragEvent, ChangeEvent, useRef } from "react";
import { Upload, X, CheckCircle, Loader2, Image as ImageIcon } from "lucide-react";
import { api } from "@/lib/api";

interface UploadZoneProps {
  onComplete?: () => void;
}

interface UploadFile {
  file: File;
  preview: string;
  status: "pending" | "uploading" | "done" | "error";
}

const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/bmp", "image/gif", "image/tiff"];

export function UploadZone({ onComplete }: UploadZoneProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const arr = Array.from(incoming).filter((f) => ACCEPTED.includes(f.type) || f.name.match(/\.(heic|bmp|tiff)$/i));
    const mapped: UploadFile[] = arr.map((f) => ({
      file: f,
      preview: URL.createObjectURL(f),
      status: "pending",
    }));
    setFiles((prev) => [...prev, ...mapped]);
  }, []);

  const onDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const onFileChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) addFiles(e.target.files);
    e.target.value = "";
  }, [addFiles]);

  const removeFile = (idx: number) => {
    setFiles((prev) => {
      URL.revokeObjectURL(prev[idx].preview);
      return prev.filter((_, i) => i !== idx);
    });
  };

  const uploadAll = async () => {
    const pending = files.filter((f) => f.status === "pending");
    if (!pending.length) return;

    setUploading(true);
    setFiles((prev) => prev.map((f) => f.status === "pending" ? { ...f, status: "uploading" } : f));

    try {
      const rawFiles = pending.map((f) => f.file);
      await api.images.upload(rawFiles);
      setFiles((prev) => prev.map((f) => f.status === "uploading" ? { ...f, status: "done" } : f));
      onComplete?.();
    } catch {
      setFiles((prev) => prev.map((f) => f.status === "uploading" ? { ...f, status: "error" } : f));
    } finally {
      setUploading(false);
    }
  };

  const clearDone = () => {
    setFiles((prev) => {
      prev.filter((f) => f.status === "done").forEach((f) => URL.revokeObjectURL(f.preview));
      return prev.filter((f) => f.status !== "done");
    });
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const doneCount = files.filter((f) => f.status === "done").length;

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
          dragging
            ? "border-accent bg-accent/5"
            : "border-white/10 hover:border-white/20 hover:bg-white/[0.02]"
        }`}
      >
        <input ref={inputRef} type="file" multiple accept="image/*" className="hidden" onChange={onFileChange} />
        <Upload className={`w-8 h-8 mx-auto mb-3 ${dragging ? "text-accent" : "text-white/30"}`} />
        <p className="text-sm text-white/50">Drag & drop images here, or click to browse</p>
        <p className="text-xs text-white/25 mt-1">JPEG, PNG, WebP, HEIC, BMP, GIF, TIFF</p>
      </div>

      {files.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/50">
              {files.length} file{files.length !== 1 ? "s" : ""}
              {doneCount > 0 && <span className="text-emerald-400"> ({doneCount} uploaded)</span>}
            </p>
            <div className="flex gap-2">
              {doneCount > 0 && (
                <button onClick={clearDone} className="px-3 py-1.5 rounded-lg text-xs text-white/40 hover:bg-white/5 transition-colors">
                  Clear done
                </button>
              )}
              {pendingCount > 0 && (
                <button
                  onClick={uploadAll}
                  disabled={uploading}
                  className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  Upload {pendingCount}
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
            {files.map((f, i) => (
              <div key={i} className="relative aspect-square rounded-lg overflow-hidden bg-surface-100 group">
                <img src={f.preview} alt="" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  {f.status === "uploading" && <Loader2 className="w-5 h-5 animate-spin text-white" />}
                  {f.status === "done" && <CheckCircle className="w-5 h-5 text-emerald-400" />}
                  {f.status === "error" && <X className="w-5 h-5 text-red-400" />}
                </div>
                {f.status === "pending" && (
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                    className="absolute top-1 right-1 p-0.5 rounded-full bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3 text-white/70" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
