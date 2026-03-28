"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

export default function SettingsPage() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    api.health()
      .then(() => setBackendStatus("ok"))
      .catch(() => setBackendStatus("error"));
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 ml-16 lg:ml-56 min-h-screen p-6">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>

        <div className="space-y-6 max-w-2xl">
          <div className="glass rounded-xl p-5">
            <h3 className="font-medium mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/60">Backend API</span>
                {backendStatus === "checking" && <Loader2 className="w-4 h-4 animate-spin text-white/30" />}
                {backendStatus === "ok" && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                {backendStatus === "error" && <XCircle className="w-4 h-4 text-red-400" />}
              </div>
            </div>
          </div>

          <div className="glass rounded-xl p-5">
            <h3 className="font-medium mb-4">Architecture</h3>
            <div className="space-y-2 text-sm text-white/50">
              <p>Backend: FastAPI + PostgreSQL + Qdrant</p>
              <p>AI: CLIP embeddings + Gemini captioning + DeepFace + YOLO</p>
              <p>Search: Hybrid (vector + structured + graph boosting)</p>
              <p>Frontend: Next.js + Tailwind CSS</p>
            </div>
          </div>

          <div className="glass rounded-xl p-5">
            <h3 className="font-medium mb-4">Quick Start</h3>
            <div className="space-y-2 text-sm text-white/40">
              <p>1. Start services: <code className="text-white/60 bg-white/5 px-1.5 py-0.5 rounded">docker compose up -d</code></p>
              <p>2. Start backend: <code className="text-white/60 bg-white/5 px-1.5 py-0.5 rounded">cd backend && uvicorn app.main:app --reload</code></p>
              <p>3. Start frontend: <code className="text-white/60 bg-white/5 px-1.5 py-0.5 rounded">cd frontend && npm run dev</code></p>
              <p>4. Go to Gallery and index a photo directory</p>
              <p>5. Search using natural language</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
