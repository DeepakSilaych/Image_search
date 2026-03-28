"use client";

import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/sidebar";
import { api, PersonData, PersonFace } from "@/lib/api";
import { UserPlus, Trash2, Users, Image as ImageIcon, Check, X, Pencil, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { ImagePreview } from "@/components/image-preview";

function PersonCard({
  person,
  onDelete,
  onRename,
  onViewImage,
}: {
  person: PersonData;
  onDelete: (id: string) => void;
  onRename: (id: string, name: string) => void;
  onViewImage: (imageId: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(person.name);
  const [expanded, setExpanded] = useState(false);
  const [faces, setFaces] = useState<PersonFace[]>([]);
  const [loadingFaces, setLoadingFaces] = useState(false);

  const toggleExpand = async () => {
    if (!expanded && faces.length === 0) {
      setLoadingFaces(true);
      try {
        const data = await api.faces.getPersonFaces(person.id);
        setFaces(data.items);
      } catch {}
      setLoadingFaces(false);
    }
    setExpanded(!expanded);
  };

  const handleRename = () => {
    if (name.trim() && name.trim() !== person.name) {
      onRename(person.id, name.trim());
    }
    setEditing(false);
  };

  return (
    <div className="glass rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-4">
        <div className="w-12 h-12 rounded-full overflow-hidden shrink-0 bg-surface-50">
          {person.representative_face_id ? (
            <img
              src={api.faces.cropUrl(person.representative_face_id, 96)}
              alt={person.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-accent font-semibold">
              {person.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex items-center gap-1">
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRename();
                  if (e.key === "Escape") { setEditing(false); setName(person.name); }
                }}
                className="px-2 py-1 rounded glass text-sm text-white focus:outline-none focus:ring-1 focus:ring-accent/50 w-full"
              />
              <button onClick={handleRename} className="p-1 text-green-400 hover:bg-green-500/10 rounded">
                <Check className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => { setEditing(false); setName(person.name); }} className="p-1 text-red-400 hover:bg-red-500/10 rounded">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <p className="text-sm font-medium truncate">{person.name}</p>
          )}
          <div className="flex items-center gap-3 mt-0.5">
            <span className="flex items-center gap-1 text-[10px] text-white/40">
              <ImageIcon className="w-3 h-3" />{person.face_count} photos
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => { setEditing(true); setName(person.name); }}
            className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all"
            title="Rename"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={toggleExpand}
            className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all"
            title="Show faces"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => onDelete(person.id)}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-all"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-white/5 p-3">
          {loadingFaces ? (
            <p className="text-xs text-white/30 text-center py-2">Loading...</p>
          ) : faces.length === 0 ? (
            <p className="text-xs text-white/30 text-center py-2">No faces</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {faces.map((f) => (
                <img
                  key={f.id}
                  src={api.faces.cropUrl(f.id, 64)}
                  alt=""
                  onClick={() => onViewImage(f.image_id)}
                  className="w-14 h-14 rounded-lg object-cover cursor-pointer hover:ring-2 hover:ring-accent/50 transition-all"
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PeoplePage() {
  const [namedPersons, setNamedPersons] = useState<PersonData[]>([]);
  const [unknownPersons, setUnknownPersons] = useState<PersonData[]>([]);
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(true);
  const [clustering, setClustering] = useState(false);
  const [tab, setTab] = useState<"named" | "unknown">("named");
  const [previewImageId, setPreviewImageId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [named, unknown] = await Promise.all([
        api.faces.listPersons("named"),
        api.faces.listPersons("unknown"),
      ]);
      setNamedPersons(named.items);
      setUnknownPersons(unknown.items);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const addPerson = async () => {
    if (!newName.trim()) return;
    try {
      await api.faces.createPerson(newName.trim());
      setNewName("");
      load();
    } catch {}
  };

  const deletePerson = async (id: string) => {
    try {
      await api.faces.deletePerson(id);
      load();
    } catch {}
  };

  const renamePerson = async (id: string, name: string) => {
    try {
      await api.faces.renamePerson(id, name);
      load();
    } catch {}
  };

  const clusterFaces = async () => {
    setClustering(true);
    try {
      await api.faces.clusterUnknown();
      load();
    } catch {}
    setClustering(false);
  };

  const currentList = tab === "named" ? namedPersons : unknownPersons;

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">People</h1>
            <p className="text-sm text-white/40">
              {namedPersons.length} known &middot; {unknownPersons.length} unknown
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={clusterFaces}
              disabled={clustering}
              className="flex items-center gap-2 px-4 py-2 rounded-lg glass hover:bg-white/5 text-white/60 hover:text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${clustering ? "animate-spin" : ""}`} />
              {clustering ? "Clustering..." : "Auto-cluster"}
            </button>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Person name..."
              className="px-3 py-2 rounded-lg glass text-sm text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-accent/50 w-48"
              onKeyDown={(e) => e.key === "Enter" && addPerson()}
            />
            <button
              onClick={addPerson}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              Add
            </button>
          </div>
        </div>

        <div className="flex gap-1 mb-6 glass rounded-lg p-1 w-fit">
          <button
            onClick={() => setTab("named")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === "named" ? "bg-accent text-white" : "text-white/50 hover:text-white"
            }`}
          >
            Named ({namedPersons.length})
          </button>
          <button
            onClick={() => setTab("unknown")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === "unknown" ? "bg-accent text-white" : "text-white/50 hover:text-white"
            }`}
          >
            Unknown ({unknownPersons.length})
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {currentList.map((p) => (
            <PersonCard
              key={p.id}
              person={p}
              onDelete={deletePerson}
              onRename={renamePerson}
              onViewImage={setPreviewImageId}
            />
          ))}
        </div>

        {!loading && currentList.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-white/30">
            <Users className="w-12 h-12 mb-3" />
            {tab === "named" ? (
              <>
                <p>No named people yet</p>
                <p className="text-sm mt-1">Name unknown faces or add people manually</p>
              </>
            ) : (
              <>
                <p>No unknown faces</p>
                <p className="text-sm mt-1">Faces will appear here as images are processed</p>
              </>
            )}
          </div>
        )}

        {previewImageId && (
          <ImagePreview imageId={previewImageId} onClose={() => setPreviewImageId(null)} />
        )}
      </main>
    </div>
  );
}
