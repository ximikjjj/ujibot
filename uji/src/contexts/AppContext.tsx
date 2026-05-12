import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { translations, type Lang, type T } from "@/lib/i18n";

type Theme = "dark" | "light";

interface AppContextValue {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  t: T;
}

const AppContext = createContext<AppContextValue | null>(null);

function getInitialLang(): Lang {
  const saved = localStorage.getItem("uji-lang") as Lang;
  if (saved === "ru" || saved === "en") return saved;
  const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user;
  const browser = navigator.language.toLowerCase();
  return browser.startsWith("ru") ? "ru" : "en";
}

function getInitialTheme(): Theme {
  const saved = localStorage.getItem("uji-theme") as Theme;
  if (saved === "dark" || saved === "light") return saved;
  const tgTheme = (window.Telegram?.WebApp as any)?.colorScheme;
  if (tgTheme === "light") return "light";
  return "dark";
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);
  const [lang, setLangState] = useState<Lang>(getInitialLang);

  useEffect(() => {
    const html = document.documentElement;
    if (theme === "dark") {
      html.classList.add("dark");
      html.classList.remove("light");
    } else {
      html.classList.remove("dark");
      html.classList.add("light");
    }
    localStorage.setItem("uji-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("uji-lang", lang);
  }, [lang]);

  const setTheme = (t: Theme) => setThemeState(t);
  const toggleTheme = () => setThemeState((p) => (p === "dark" ? "light" : "dark"));
  const setLang = (l: Lang) => setLangState(l);

  return (
    <AppContext.Provider value={{ theme, toggleTheme, setTheme, lang, setLang, t: translations[lang] }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
