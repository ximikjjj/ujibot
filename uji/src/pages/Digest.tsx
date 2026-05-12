import { useEffect, useState } from "react";
import { api, getTelegramId, type Digest } from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

function Section({ icon, label, children }: { icon: string; label: string; children: React.ReactNode }) {
  return (
    <div className="p-4 rounded-xl bg-card border border-border/60 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-base">{icon}</span>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{label}</p>
      </div>
      <div className="text-sm text-foreground leading-relaxed">{children}</div>
    </div>
  );
}

export default function DigestPage() {
  const { t, lang } = useApp();
  const tgId = getTelegramId();
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.getDigest(tgId).then(setDigest).catch(() => {}).finally(() => setLoading(false));
  }, [tgId]);

  async function refresh() {
    setGenerating(true);
    try {
      const d = await api.getDigest(tgId);
      setDigest(d);
    } catch {} finally { setGenerating(false); }
  }

  const today = new Date().toLocaleDateString(lang === "ru" ? "ru" : "en", { day: "numeric", month: "long" });

  return (
    <div className="pb-24 px-4 pt-4 space-y-4">
      <div className="pt-2 pb-1 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-tight">{t.digest.title}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{today}</p>
        </div>
        <button
          onClick={refresh}
          disabled={generating}
          className="text-xs text-primary border border-primary/30 px-3 py-1.5 rounded-full hover:bg-primary/10 transition-colors disabled:opacity-40"
        >
          {generating ? t.digest.generating : t.digest.refresh}
        </button>
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-24 rounded-xl bg-card animate-pulse" />)}
        </div>
      )}

      {!loading && !digest && (
        <div className="mt-12 text-center space-y-3">
          <p className="text-muted-foreground text-sm">{t.digest.noData}</p>
          <p className="text-xs text-muted-foreground">{t.digest.noDataDesc}</p>
        </div>
      )}

      {digest && (
        <>
          {digest.what_worked && <Section icon="✓" label={t.digest.whatWorked}>{digest.what_worked}</Section>}
          {digest.near_misses && <Section icon="!" label={t.digest.nearMisses}>{digest.near_misses}</Section>}
          {digest.best_reply && <Section icon="★" label={t.digest.bestReply}>{digest.best_reply}</Section>}
          {digest.funniest_moment && <Section icon="~" label={t.digest.funniest}>{digest.funniest_moment}</Section>}
          {digest.dead_dialogs.length > 0 && (
            <Section icon="×" label={t.digest.deadDialogs}>
              <ul className="space-y-1">
                {digest.dead_dialogs.map((d, i) => <li key={i} className="text-muted-foreground">{d}</li>)}
              </ul>
            </Section>
          )}
          {Object.keys(digest.goals_progress).length > 0 && (
            <Section icon="→" label={t.digest.goalsProgress}>
              <ul className="space-y-1.5">
                {Object.entries(digest.goals_progress).map(([goal, progress]) => (
                  <li key={goal} className="flex gap-2 items-start">
                    <span className="text-primary font-bold shrink-0">—</span>
                    <span><span className="text-foreground">{goal}:</span> <span className="text-muted-foreground">{progress as string}</span></span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </>
      )}
    </div>
  );
}
