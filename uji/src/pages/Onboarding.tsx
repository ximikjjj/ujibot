import { useState } from "react";
import { useApp } from "@/contexts/AppContext";

const steps = [
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-primary">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    key: "step1" as const,
  },
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-primary">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 8v4l3 3"/>
      </svg>
    ),
    key: "step2" as const,
  },
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-primary">
        <path d="M20 6L9 17l-5-5"/>
      </svg>
    ),
    key: "step3" as const,
  },
];

export default function Onboarding({ onDone }: { onDone: () => void }) {
  const { t } = useApp();
  const [step, setStep] = useState(0);

  const current = steps[step];
  const titleKey = `${current.key}Title` as "step1Title" | "step2Title" | "step3Title";
  const descKey = `${current.key}Desc` as "step1Desc" | "step2Desc" | "step3Desc";
  const isLast = step === steps.length - 1;

  return (
    <div className="min-h-screen flex flex-col items-center justify-between px-6 pt-16 pb-12 animate-fade-in">
      <button
        onClick={onDone}
        className="self-end text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        {t.onboarding.skip}
      </button>

      <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6 max-w-xs">
        <div className="w-20 h-20 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          {current.icon}
        </div>

        <div className="space-y-3">
          <h1 className="text-2xl font-bold tracking-tight">{t.onboarding[titleKey]}</h1>
          <p className="text-muted-foreground leading-relaxed">{t.onboarding[descKey]}</p>
        </div>
      </div>

      <div className="w-full space-y-5">
        <div className="flex justify-center gap-2">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === step ? "w-6 bg-primary" : "w-1.5 bg-muted"
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => (isLast ? onDone() : setStep((s) => s + 1))}
          className="w-full py-3.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm"
        >
          {isLast ? t.onboarding.start : t.onboarding.next}
        </button>
      </div>
    </div>
  );
}
