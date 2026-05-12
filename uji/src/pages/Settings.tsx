import { useApp } from "@/contexts/AppContext";
import { api, getTelegramId } from "@/lib/api";
import { useLocation } from "wouter";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3.5 px-4">
      <span className="text-sm font-medium">{label}</span>
      <div>{children}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-0.5">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4 pb-1">{title}</p>
      <div className="rounded-xl border border-border/60 bg-card divide-y divide-border/40 overflow-hidden">
        {children}
      </div>
    </div>
  );
}

function Toggle({ active, onToggle }: { active: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${active ? "bg-primary" : "bg-muted"}`}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${active ? "translate-x-5" : "translate-x-0"}`}
      />
    </button>
  );
}

export default function Settings() {
  const { t, theme, toggleTheme, lang, setLang } = useApp();
  const [, setLocation] = useLocation();
  const tgId = getTelegramId();

  async function disconnect() {
    try {
      await fetch(`/bot-api/session/status/${tgId}`);
    } catch {}
    setLocation("/connect");
  }

  return (
    <div className="pb-28 px-4 pt-4 space-y-5">
      <div className="pt-2 pb-1">
        <h1 className="text-lg font-bold tracking-tight">{t.settings.title}</h1>
      </div>

      <Section title={t.settings.appearance}>
        <Row label={t.settings.theme}>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {theme === "dark" ? t.settings.themeDark : t.settings.themeLight}
            </span>
            <Toggle active={theme === "dark"} onToggle={toggleTheme} />
          </div>
        </Row>
      </Section>

      <Section title={t.settings.language}>
        <Row label={t.settings.language}>
          <div className="flex rounded-lg overflow-hidden border border-border/60">
            <button
              onClick={() => setLang("ru")}
              className={`px-3.5 py-1.5 text-sm font-medium transition-colors ${
                lang === "ru" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              RU
            </button>
            <button
              onClick={() => setLang("en")}
              className={`px-3.5 py-1.5 text-sm font-medium transition-colors ${
                lang === "en" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              EN
            </button>
          </div>
        </Row>
      </Section>

      <Section title={t.settings.about}>
        <div className="px-4 py-3.5 space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-primary">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold">UJI</p>
              <p className="text-xs text-muted-foreground">{t.settings.version}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed pt-1">{t.settings.description}</p>
        </div>
      </Section>
    </div>
  );
}
