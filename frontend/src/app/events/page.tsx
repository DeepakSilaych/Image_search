"use client";

import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/sidebar";
import { api, EventData } from "@/lib/api";
import { Calendar, MapPin, Image as ImageIcon, Wand2, Loader2 } from "lucide-react";

export default function EventsPage() {
  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await api.events.list();
      setEvents(data.items);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const detectEvents = async () => {
    setDetecting(true);
    try {
      const result = await api.events.detect();
      load();
    } catch {}
    setDetecting(false);
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Events</h1>
            <p className="text-sm text-white/40">{events.length} events detected</p>
          </div>
          <button
            onClick={detectEvents}
            disabled={detecting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            {detecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            Auto-Detect Events
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map((evt) => (
            <div key={evt.id} className="glass rounded-xl p-5 space-y-3">
              <h3 className="font-semibold">{evt.name}</h3>
              {evt.description && <p className="text-sm text-white/50">{evt.description}</p>}
              <div className="flex flex-wrap gap-3 text-xs text-white/40">
                {evt.start_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(evt.start_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </span>
                )}
                {evt.location_name && (
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{evt.location_name}</span>
                )}
                <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3" />{evt.image_count} photos</span>
              </div>
              {evt.auto_generated && (
                <span className="inline-block px-2 py-0.5 rounded bg-amber-500/10 text-[10px] text-amber-400">auto-detected</span>
              )}
            </div>
          ))}
        </div>

        {!loading && events.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-white/30">
            <Calendar className="w-12 h-12 mb-3" />
            <p>No events yet</p>
            <p className="text-sm mt-1">Index photos with timestamps and click Auto-Detect to cluster them into events</p>
          </div>
        )}
      </main>
    </div>
  );
}
