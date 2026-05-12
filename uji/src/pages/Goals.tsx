import { useEffect, useState } from "react";
import { api, getTelegramId, type Goal } from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

export default function Goals() {
  const { t } = useApp();
  const tgId = getTelegramId();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  useEffect(() => {
    api.getGoals(tgId).then(setGoals).catch(() => {}).finally(() => setLoading(false));
  }, [tgId]);

  async function addGoal(text: string) {
    if (!text.trim() || adding) return;
    setAdding(true);
    try {
      const g = await api.addGoal(tgId, text.trim());
      setGoals((prev) => [...prev, g]);
      setInput("");
    } catch {} finally { setAdding(false); }
  }

  async function removeGoal(id: number) {
    await api.deleteGoal(tgId, id).catch(() => {});
    setGoals((prev) => prev.filter((g) => g.id !== id));
    setConfirmDelete(null);
  }

  const activeTexts = new Set(goals.map((g) => g.text));

  return (
    <div className="pb-24 px-4 pt-4 space-y-5">
      <div className="pt-2 pb-1">
        <h1 className="text-lg font-bold tracking-tight">{t.goals.title}</h1>
        <p className="text-xs text-muted-foreground mt-0.5">{t.goals.subtitle}</p>
      </div>

      <div className="flex gap-2">
        <input
          data-testid="input-goal"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addGoal(input)}
          placeholder={t.goals.inputPlaceholder}
          className="flex-1 bg-card border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <button
          data-testid="button-add-goal"
          onClick={() => addGoal(input)}
          disabled={!input.trim() || adding}
          className="px-4 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-40"
        >
          +
        </button>
      </div>

      {(loading || goals.length > 0) && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider px-1">{t.goals.active}</p>
          {loading && <div className="h-16 rounded-xl bg-card animate-pulse" />}
          {goals.map((g) => (
            <div key={g.id} data-testid={`goal-item-${g.id}`} className="rounded-xl bg-card border border-border/60 animate-slide-up overflow-hidden">
              <div className="flex items-center gap-3 p-3.5">
                <div className="w-2 h-2 rounded-full bg-primary shrink-0 animate-pulse-glow" />
                <span className="flex-1 text-sm">{g.text}</span>
                {g.progress_count > 0 && (
                  <span className="text-xs text-emerald-400 font-medium bg-emerald-400/10 px-2 py-0.5 rounded-full">
                    {g.progress_count}x
                  </span>
                )}
                <button
                  data-testid={`button-delete-goal-${g.id}`}
                  onClick={() => setConfirmDelete(g.id)}
                  className="text-muted-foreground hover:text-destructive transition-colors p-1"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              {confirmDelete === g.id && (
                <div className="flex items-center justify-between px-3.5 py-2.5 bg-destructive/8 border-t border-destructive/20">
                  <span className="text-xs text-destructive font-medium">{t.goals.deleteConfirm}</span>
                  <div className="flex gap-2">
                    <button onClick={() => setConfirmDelete(null)} className="text-xs text-muted-foreground px-2.5 py-1 rounded-lg border border-border">
                      ✕
                    </button>
                    <button onClick={() => removeGoal(g.id)} className="text-xs text-destructive px-2.5 py-1 rounded-lg border border-destructive/30 bg-destructive/10">
                      ✓
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider px-1">{t.goals.quick}</p>
        <div className="flex flex-wrap gap-2">
          {t.goals.presets.filter((p) => !activeTexts.has(p)).map((p) => (
            <button
              key={p}
              onClick={() => addGoal(p)}
              className="text-xs px-3 py-1.5 rounded-full border border-border/60 bg-card hover:border-primary/40 hover:text-primary transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
