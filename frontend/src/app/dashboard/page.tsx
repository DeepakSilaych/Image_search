"use client";

import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { useStats } from "@/hooks/use-stats";
import { Images, Users, Calendar, Eye, Box, FileText, Database, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const { stats, loading } = useStats();

  if (loading || !stats) {
    return (
      <div className="flex">
        <Sidebar />
        <main className="flex-1 ml-16 lg:ml-56 min-h-screen flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-white/30" />
        </main>
      </div>
    );
  }

  const sceneEntries = Object.entries(stats.scene_distribution).sort((a, b) => b[1] - a[1]);
  const typeEntries = Object.entries(stats.type_distribution).sort((a, b) => b[1] - a[1]);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Images" value={stats.images.total} icon={<Images className="w-5 h-5" />} />
          <StatCard label="Processed" value={stats.images.processed} icon={<Eye className="w-5 h-5" />} color="text-emerald-400" />
          <StatCard label="People" value={stats.persons} icon={<Users className="w-5 h-5" />} color="text-amber-400" />
          <StatCard label="Events" value={stats.events} icon={<Calendar className="w-5 h-5" />} color="text-cyan-400" />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Faces Detected" value={stats.faces_detected} icon={<Users className="w-5 h-5" />} color="text-pink-400" />
          <StatCard label="Objects Detected" value={stats.objects_detected} icon={<Box className="w-5 h-5" />} color="text-orange-400" />
          <StatCard label="Image Vectors" value={stats.vectors.images} icon={<Database className="w-5 h-5" />} color="text-violet-400" />
          <StatCard label="Pending" value={stats.images.pending} icon={<FileText className="w-5 h-5" />} color="text-yellow-400" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-medium text-white/60 mb-4">Scene Distribution</h3>
            <div className="space-y-2">
              {sceneEntries.slice(0, 10).map(([scene, count]) => {
                const pct = stats.images.processed > 0 ? (count / stats.images.processed) * 100 : 0;
                return (
                  <div key={scene} className="flex items-center gap-3">
                    <span className="text-xs text-white/50 w-20 truncate">{scene}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                      <div className="h-full rounded-full bg-accent/50" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-xs text-white/30 w-8 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-medium text-white/60 mb-4">Image Types</h3>
            <div className="space-y-2">
              {typeEntries.slice(0, 10).map(([type, count]) => {
                const pct = stats.images.processed > 0 ? (count / stats.images.processed) * 100 : 0;
                return (
                  <div key={type} className="flex items-center gap-3">
                    <span className="text-xs text-white/50 w-20 truncate">{type}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500/50" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-xs text-white/30 w-8 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
