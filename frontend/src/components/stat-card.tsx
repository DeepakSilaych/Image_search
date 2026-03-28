interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  color?: string;
}

export function StatCard({ label, value, icon, color = "text-accent" }: StatCardProps) {
  return (
    <div className="glass rounded-xl p-4 flex items-center gap-4">
      <div className={`p-2.5 rounded-lg bg-white/5 ${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-semibold">{value}</p>
        <p className="text-xs text-white/40">{label}</p>
      </div>
    </div>
  );
}
