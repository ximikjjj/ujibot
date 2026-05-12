import { useEffect, useState } from "react";
import { api, getTelegramId, type Stats } from "@/lib/api";

const SCALES = [
  { key: "confidence" as keyof Stats, label: "Уверенность", color: "#3b82f6", desc: "Насколько ты звучишь уверенно" },
  { key: "ease" as keyof Stats, label: "Лёгкость", color: "#22c55e", desc: "Комфорт и непринуждённость в диалоге" },
  { key: "tension" as keyof Stats, label: "Напряжение", color: "#f97316", desc: "Уровень стресса в переписке" },
  { key: "initiative" as keyof Stats, label: "Инициатива", color: "#a855f7", desc: "Ты ведёшь диалог или отвечаешь" },
  { key: "warmth" as keyof Stats, label: "Теплота", color: "#ec4899", desc: "Эмоциональная близость в общении" },
  { key: "clarity" as keyof Stats, label: "Ясность", color: "#06b6d4", desc: "Насколько тебя понимают" },
];

function ScaleBar({ label, value, color, desc }: { label: string; value: number; color: string; desc: string }) {
  const [animated, setAnimated] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setAnimated(value), 80);
    return () => clearTimeout(t);
  }, [value]);

  const intensity = value >= 70 ? "отлично" : value >= 45 ? "норма" : "слабо";
  const intensityColor = value >= 70 ? "text-emerald-400" : value >= 45 ? "text-yellow-400" : "text-red-400";

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

export default function Scales() {
  const tgId = getTelegramId();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats(tgId).then(setStats).catch(() => {}).finally(() => setLoading(false));
  }, [tgId]);

  const avg = stats ? Math.round(Object.values(stats).filter(v => typeof v === "number").reduce((a: number, b) => a + (b as number), 0) / 6) : 0;

  return (
    <div className="pb-24 px-4 pt-4 space-y-4">
      <div className="pt-2 pb-1">
        <h1 className="text-lg font-bold tracking-tight">Шкалы общения</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Обновляются после каждого диалога</p>
      </div>

      {!loading && stats && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-primary/8 border border-primary/20">
          <div className="text-3xl font-bold text-primary tabular-nums">{avg}</div>
          <div>
            <p className="text-sm font-semibold">Общий уровень</p>
            <p className="text-xs text-muted-foreground">среднее по всем шкалам</p>
          </div>
        </div>
      )}

      {loading && <div className="space-y-3">{[1,2,3,4,5,6].map(i => <div key={i} className="h-24 rounded-xl bg-card animate-pulse" />)}</div>}

      {stats && SCALES.map(s => (
        <ScaleBar key={s.key} label={s.label} value={stats[s.key] as number} color={s.color} desc={s.desc} />
      ))}
    </div>
  );
}
