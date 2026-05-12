declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        initDataUnsafe?: { user?: { id?: number; first_name?: string; username?: string } };
      };
    };
  }
}

export function getTelegramId(): number {
  return window.Telegram?.WebApp?.initDataUnsafe?.user?.id ?? 999999;
}

const BASE = "/bot-api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getUser: (id: number) => req<UserProfile>(`/user/${id}`),
  getSessionStatus: (id: number) => req<SessionStatus>(`/session/status/${id}`),
  getSuggestions: (id: number, limit = 20) =>
    req<Suggestion[]>(`/user/${id}/suggestions?limit=${limit}`),
  getStats: (id: number) => req<Stats>(`/user/${id}/stats`),
  getGoals: (id: number) => req<Goal[]>(`/user/${id}/goals`),
  addGoal: (id: number, text: string) =>
    req<Goal>(`/user/${id}/goals`, { method: "POST", body: JSON.stringify({ text }) }),
  deleteGoal: (id: number, goalId: number) =>
    req<{ success: boolean }>(`/user/${id}/goals/${goalId}`, { method: "DELETE" }),
  getDigest: (id: number) => req<Digest>(`/user/${id}/digest`),
  startSession: (telegram_id: number, phone: string) =>
    req<{ status: string }>(`/session/start`, {
      method: "POST",
      body: JSON.stringify({ telegram_id, phone }),
    }),
  verifySession: (telegram_id: number, code: string, password?: string) =>
    req<{ status: string; message: string }>(`/session/verify`, {
      method: "POST",
      body: JSON.stringify({ telegram_id, code, password }),
    }),
  sendChat: (telegram_id: number, message: string, history: ChatMessage[]) =>
    req<{ reply: string }>(`/chat`, {
      method: "POST",
      body: JSON.stringify({ telegram_id, message, history }),
    }),
};

export interface UserProfile {
  telegram_id: number;
  username?: string;
  first_name?: string;
  phone?: string;
  is_session_active: boolean;
}

export interface SessionStatus {
  telegram_id: number;
  is_connected: boolean;
  has_session: boolean;
  phone?: string;
}

export interface Suggestion {
  id: number;
  incoming_message: string;
  analysis?: string;
  variants: string[];
  tone?: string;
  created_at: string;
}

export interface Stats {
  confidence: number | null;
  ease: number | null;
  tension: number | null;
  initiative: number | null;
  warmth: number | null;
  clarity: number | null;
  no_data?: boolean;
}

export interface Goal {
  id: number;
  text: string;
  progress_count: number;
}

export interface Digest {
  date: string;
  what_worked?: string;
  near_misses?: string;
  best_reply?: string;
  funniest_moment?: string;
  dead_dialogs: string[];
  goals_progress: Record<string, string>;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
