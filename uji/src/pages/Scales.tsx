import { useEffect, useState } from "react";
import { api, getTelegramId, type Stats } from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

export default function Scales() {
  const { t } = useApp();
  const tgId = getTelegramId();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const SCALES = [
    { key: "confidence" as keyof Stats, label: t.scales.confidence, color: "#3b82f6", desc: t.scales.confidenceDesc },
    { key: "ease" as keyof Stats, label: t.scales.ease, color: "#22c55e", desc: t.scales.easeDesc },
    { key: "tension" as keyof Stats, label: t.scales.tension, color: "#f97316", desc: t.scales.tensionDesc },
    { key: "initiative" as keyof Stats, label: t.scales.initiative, color: "#a855f7", desc: t.scales.initiativeDesc },
    { key: "warmth" as keyof Stats, label: t.scales.warmth, color: "#ec4899", desc: t.scales.warmthDesc },
    { key: "clarity" as keyof Stats, label: t.scales.clarity, color: "#06b6d4", desc: t.scales.clarityDesc },
  ];

  useEffect(() => {
    api.getStats(tgId).then(setStats).catch(() => {}).finally(() => setLoading(false));
  }, [tgId]);

  const avg = stats
    ? Math.round(Object.values(stats).filter((v) => typeof v === "number").reduce((a: number, b) => a + (b as number), 0) / 6)
    : 0;

  return (
    <div className="pb-24 px-4 pt-4 space-y-4">
      <div className="pt-2 pb-1">
        <h1 className="text-lg font-bold tracking-tight">{t.scales.title}</h1>
        <p className="text-xs text-muted-foreground mt-0.5">{t.scales.subtitle}</p>
      </div>

      {!loading && stats && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-primary/8 border border-primary/20">
          <div className="text-3xl font-bold text-primary tabular-nums">{avg}</div>
          <div>
            <p className="text-sm font-semibold">{t.scales.overall}</p>
            <p className="text-xs text-muted-foreground">{t.scales.overallSub}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="h-24 rounded-xl bg-card animate-pulse" />)}
        </div>
      )}

      {stats && SCALES.map((s) => {
        const value = stats[s.key] as number;
        const intensity = value >= 70 ? t.scales.great : value >= 45 ? t.scales.normal : t.scales.weak;
        const intensityColor = value >= 70 ? "text-emerald-400" : value >= 45 ? "text-yellow-400" : "text-red-400";

        return (
          <ScaleBar
            key={s.key}
            label={s.label}
            value={value}
            color={s.color}
            desc={s.desc}
            intensity={intensity}
            intensityColor={intensityColor}
          />
        );
      })}
    </div>
  );
}

function ScaleBar({
  label, value, color, desc, intensity, intensityColor,
}: {
  label: string; value: number; color: string; desc: string; intensity: string; intensityColor: string;
}) {
  const [animated, setAnimated] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setAnimated(value), 80);
    return () => clearTimeout(t);
  }, [value]);

  return (
    <div className="space-y-2.5 p-4 rounded-xl bg-card border border-border/60">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold">{label}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold tabular-nums" style={{ color }}>{value}</p>
          <p className={`text-xs font-medium ${intensityColor}`}>{intensity}</p>
        </div>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${animated}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
