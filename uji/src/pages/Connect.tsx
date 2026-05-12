import { useState } from "react";
import { useLocation } from "wouter";
import { api, getTelegramId } from "@/lib/api";

type Step = "phone" | "code" | "password" | "done";

export default function Connect() {
  const [, setLocation] = useLocation();
  const tgId = getTelegramId();
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submitPhone() {
    if (!phone.trim()) return;
    setLoading(true); setError("");
    try {
      await api.startSession(tgId, phone.trim());
      setStep("code");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally { setLoading(false); }
  }

  async function submitCode() {
    if (!code.trim()) return;
    setLoading(true); setError("");
    try {
      const res = await api.verifySession(tgId, code.trim());
      if (res.status === "need_password") { setStep("password"); return; }
      if (res.status === "success") { setStep("done"); return; }
      setError(res.message || "Ошибка");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally { setLoading(false); }
  }

  async function submitPassword() {
    if (!password.trim()) return;
    setLoading(true); setError("");
    try {
      const res = await api.verifySession(tgId, code, password.trim());
      if (res.status === "success") { setStep("done"); return; }
      setError(res.message || "Ошибка");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally { setLoading(false); }
  }

  if (step === "done") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 pb-24 text-center space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-emerald-400"><path d="M20 6L9 17l-5-5"/></svg>
        </div>
        <div>
          <p className="text-lg font-semibold">Сессия подключена</p>
          <p className="text-sm text-muted-foreground mt-1">UJI теперь видит входящие сообщения<br/>и будет подсказывать в реальном времени</p>
        </div>
        <button onClick={() => setLocation("/")} className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold">
          На главную
        </button>
      </div>
    );
  }

  const steps = { phone: 1, code: 2, password: 3, done: 3 };
  const labels = { phone: "Номер телефона", code: "Код из Telegram", password: "Пароль 2FA" };

  return (
    <div className="min-h-screen pb-24 px-4 pt-8 space-y-8">
      <div>
        <button onClick={() => setLocation("/")} className="text-muted-foreground text-sm flex items-center gap-1.5 mb-6">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5m7-7-7 7 7 7"/></svg>
          Назад
        </button>
        <h1 className="text-xl font-bold tracking-tight">Подключение сессии</h1>
        <p className="text-sm text-muted-foreground mt-1">UJI подключится к твоему Telegram как клиент<br/>и начнёт читать переписки в реальном времени</p>
      </div>

      <div className="flex gap-2">
        {[1, 2, 3].map(n => (
          <div key={n} className={`h-1 flex-1 rounded-full transition-colors ${n <= steps[step] ? "bg-primary" : "bg-muted"}`} />
        ))}
      </div>

      <div className="space-y-4">
        <label className="block text-sm font-medium text-foreground">{labels[step]}</label>
        {step === "phone" && (
          <>
            <input
              data-testid="input-phone"
              type="tel" value={phone} onChange={e => setPhone(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submitPhone()}
              placeholder="+79991234567"
              className="w-full bg-card border border-border rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground">Введи номер телефона привязанный к Telegram</p>
          </>
        )}
        {step === "code" && (
          <>
            <input
              data-testid="input-code"
              type="text" value={code} onChange={e => setCode(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submitCode()}
              placeholder="12345"
              maxLength={7}
              className="w-full bg-card border border-border rounded-xl px-4 py-3 text-2xl font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground text-center">Telegram отправил тебе код в приложении</p>
          </>
        )}
        {step === "password" && (
          <>
            <input
              data-testid="input-password"
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submitPassword()}
              placeholder="Пароль двухфакторной аутентификации"
              className="w-full bg-card border border-border rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </>
        )}
        {error && <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-2.5">{error}</p>}
        <button
          data-testid="button-submit"
          onClick={step === "phone" ? submitPhone : step === "code" ? submitCode : submitPassword}
          disabled={loading}
          className="w-full py-3 rounded-xl bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50 transition-opacity"
        >
          {loading ? "Отправляю..." : step === "phone" ? "Получить код" : step === "code" ? "Подтвердить" : "Войти"}
        </button>
      </div>
    </div>
  );
}
