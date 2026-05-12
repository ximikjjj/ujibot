import { useState, useEffect, useRef } from "react";
import { useLocation } from "wouter";
import { api, getTelegramId, type Suggestion, type SessionStatus } from "@/lib/api";

function ToneTag({ tone }: { tone?: string }) {
  const map: Record<string, { label: string; color: string }> = {
    cold: { label: "холодно", color: "text-blue-400 bg-blue-400/10" },
    neutral: { label: "нейтрально", color: "text-slate-400 bg-slate-400/10" },
    warm: { label: "тепло", color: "text-orange-400 bg-orange-400/10" },
    tense: { label: "напряжение", color: "text-red-400 bg-red-400/10" },
    flirty: { label: "флирт", color: "text-pink-400 bg-pink-400/10" },
  };
  const t = map[tone ?? ""] ?? { label: tone ?? "?", color: "text-muted-foreground bg-muted" };
  return <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${t.color}`}>{t.label}</span>;
}

function SuggestionCard({ s, isNew }: { s: Suggestion; isNew?: boolean }) {
  return (
    <div className={`rounded-xl border border-border/70 bg-card p-4 space-y-3 ${isNew ? "animate-slide-up" : ""}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-muted-foreground leading-snug line-clamp-2">"{s.incoming_message}"</p>
        <ToneTag tone={s.tone} />
      </div>
      {s.analysis && <p className="text-xs text-foreground/70 leading-relaxed border-l-2 border-primary/40 pl-3">{s.analysis}</p>}
      {s.variants.length > 0 && (
        <div className="space-y-1.5">
          {s.variants.map((v, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="text-primary text-xs font-bold mt-0.5 shrink-0">{i + 1}</span>
              <p className="text-sm text-foreground leading-snug">{v}</p>
            </div>
          ))}
        </div>
      )}
      <p className="text-[10px] text-muted-foreground">{new Date(s.created_at).toLocaleTimeString("ru", { hour: "2-digit", minute: "2-digit" })}</p>
    </div>
  );
}

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const tgId = getTelegramId();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [liveIds, setLiveIds] = useState<Set<number>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    Promise.all([
      api.getSuggestions(tgId).then(setSuggestions).catch(() => {}),
      api.getSessionStatus(tgId).then(setStatus).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [tgId]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/bot-api/ws/${tgId}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "suggestion") {
          const newS: Suggestion = {
            id: Date.now(),
            incoming_message: msg.message,
            analysis: msg.data.analysis,
            variants: msg.data.variants ?? [],
            tone: msg.data.tone,
            created_at: new Date().toISOString(),
          };
          setSuggestions((prev) => [newS, ...prev].slice(0, 15));
          setLiveIds((prev) => new Set([...prev, newS.id]));
          setTimeout(() => setLiveIds((prev) => { const n = new Set(prev); n.delete(newS.id); return n; }), 600);
        }
      } catch {}
    };
    return () => ws.close();
  }, [tgId]);

  return (
    <div className="pb-24">
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-md border-b border-border/50 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`w-2 h-2 rounded-full ${status?.is_connected ? "bg-emerald-400 animate-pulse-glow" : "bg-slate-600"}`} />
          <span className="text-sm font-semibold tracking-tight">UJI</span>
          <span className="text-xs text-muted-foreground">{status?.is_connected ? "слушает" : "не подключён"}</span>
        </div>
        {!status?.is_connected && (
          <button onClick={() => setLocation("/connect")} className="text-xs text-primary font-medium border border-primary/30 px-3 py-1 rounded-full hover:bg-primary/10 transition-colors">
            Подключить
          </button>
        )}
      </div>

      <div className="px-4 pt-4 space-y-3">
        {loading && (
          <div className="space-y-3">
            {[1,2,3].map(i => <div key={i} className="h-28 rounded-xl bg-card animate-pulse" />)}
          </div>
        )}
        {!loading && suggestions.length === 0 && (
          <div className="mt-16 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-card border border-border/60 flex items-center justify-center">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-muted-foreground"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div>
              <p className="text-foreground font-medium">Нет активных подсказок</p>
              <p className="text-sm text-muted-foreground mt-1">UJI начнёт подсказывать когда<br/>получишь новые сообщения</p>
            </div>
            {!status?.is_connected && (
              <button onClick={() => setLocation("/connect")} className="mt-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold">
                Подключить сессию
              </button>
            )}
          </div>
        )}
        {!loading && suggestions.map((s) => (
          <SuggestionCard key={s.id} s={s} isNew={liveIds.has(s.id)} />
        ))}
      </div>
    </div>
  );
}
