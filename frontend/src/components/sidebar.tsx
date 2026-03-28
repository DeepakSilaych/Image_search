"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search, Images, Users, Calendar, BarChart3, Settings, Sparkles,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", icon: Search, label: "Search" },
  { href: "/gallery", icon: Images, label: "Gallery" },
  { href: "/people", icon: Users, label: "People" },
  { href: "/events", icon: Calendar, label: "Events" },
  { href: "/dashboard", icon: BarChart3, label: "Dashboard" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-16 lg:w-56 flex flex-col bg-surface-50 border-r border-white/5 z-50">
      <div className="flex items-center gap-2 px-4 h-14 border-b border-white/5">
        <Sparkles className="w-5 h-5 text-accent shrink-0" />
        <span className="hidden lg:block text-sm font-semibold tracking-tight">Memory Engine</span>
      </div>

      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-accent/15 text-accent"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="hidden lg:block">{label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
