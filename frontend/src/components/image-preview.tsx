"use client";

import { useEffect, useState } from "react";
import { X, MapPin, Clock, Tag, User, Box, Check, Pencil } from "lucide-react";
import { api, ImageData } from "@/lib/api";

interface ImagePreviewProps {
  imageId: string;
  onClose: () => void;
}

export function ImagePreview({ imageId, onClose }: ImagePreviewProps) {
  const [image, setImage] = useState<ImageData | null>(null);

  const reload = () => api.images.get(imageId).then(setImage).catch(() => {});

  useEffect(() => { reload(); }, [imageId]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={onClose}>
      <div className="relative flex max-w-6xl max-h-[90vh] w-full mx-4 glass rounded-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-3 right-3 z-10 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors">
          <X className="w-4 h-4" />
        </button>

        <div className="flex-1 flex items-center justify-center bg-black/40 min-w-0">
          <img
            src={api.images.fileUrl(imageId)}
            alt={image?.caption || ""}
            className="max-w-full max-h-[90vh] object-contain"
          />
        </div>

        {image && (
          <div className="w-80 shrink-0 p-5 overflow-y-auto border-l border-white/5 space-y-5">
            {image.caption && (
              <div>
                <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-1">Caption</h3>
                <p className="text-sm text-white/80">{image.caption}</p>
              </div>
            )}

            <MetadataSection icon={Clock} label="Date" value={image.taken_at ? new Date(image.taken_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) : null} />
            <MetadataSection icon={MapPin} label="Location" value={image.location_name} />
            <MetadataSection icon={Tag} label="Scene" value={image.scene_type} />
            <MetadataSection icon={Tag} label="Type" value={image.image_type} />

            {image.faces.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-3">People</h3>
                <div className="space-y-2">
                  {image.faces.map((f) => (
                    <FaceCard key={f.id} face={f} onNamed={reload} />
                  ))}
                </div>
              </div>
            )}

            {image.objects.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-2">Objects</h3>
                <div className="flex flex-wrap gap-1.5">
                  {image.objects.map((o) => (
                    <span key={o.id} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 text-xs text-white/60">
                      <Box className="w-3 h-3" />{o.label}
                      <span className="text-white/30">{(o.confidence * 100).toFixed(0)}%</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {image.ocr_text && (
              <div>
                <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-1">Text (OCR)</h3>
                <p className="text-xs text-white/50 bg-white/5 rounded-lg p-2 max-h-32 overflow-y-auto">
                  {image.ocr_text}
                </p>
              </div>
            )}

            <div className="pt-2 border-t border-white/5">
              <p className="text-[10px] text-white/20 break-all">{image.file_path}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FaceCard({
  face,
  onNamed,
}: {
  face: ImageData["faces"][number];
  onNamed: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const isUnknown = !face.person_name;

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await api.faces.nameFace(face.id, name.trim());
      setEditing(false);
      setName("");
      onNamed();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-center gap-3 p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.05] transition-colors">
      <img
        src={api.faces.cropUrl(face.id)}
        alt={face.person_name || "Unknown face"}
        className="w-12 h-12 rounded-lg object-cover bg-white/5 shrink-0"
      />
      <div className="flex-1 min-w-0">
        {editing ? (
          <div className="flex items-center gap-1">
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              placeholder="Enter name"
              className="flex-1 min-w-0 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-xs text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-accent/50"
              disabled={saving}
            />
            <button
              onClick={handleSave}
              disabled={saving || !name.trim()}
              className="p-1 rounded-md bg-accent hover:bg-accent-hover text-white disabled:opacity-40 transition-colors"
            >
              <Check className="w-3 h-3" />
            </button>
            <button
              onClick={() => { setEditing(false); setName(""); }}
              className="p-1 rounded-md hover:bg-white/10 text-white/40 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <span className={`text-xs font-medium truncate ${isUnknown ? "text-white/40 italic" : "text-white/80"}`}>
              {face.person_name || "Unknown"}
            </span>
            <button
              onClick={() => setEditing(true)}
              className="p-0.5 rounded hover:bg-white/10 text-white/20 hover:text-white/60 transition-colors"
              title={isUnknown ? "Name this person" : "Rename"}
            >
              <Pencil className="w-3 h-3" />
            </button>
          </div>
        )}
        {face.emotion && (
          <span className="text-[10px] text-white/30">{face.emotion}</span>
        )}
      </div>
    </div>
  );
}

function MetadataSection({ icon: Icon, label, value }: { icon: any; label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2">
      <Icon className="w-3.5 h-3.5 text-white/30 mt-0.5 shrink-0" />
      <div>
        <p className="text-[10px] text-white/30 uppercase tracking-wider">{label}</p>
        <p className="text-xs text-white/70">{value}</p>
      </div>
    </div>
  );
}
