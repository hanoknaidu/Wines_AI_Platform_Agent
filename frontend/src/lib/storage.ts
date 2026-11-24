import { config } from "../config";
import type { Conversation } from "../types";

interface Stored {
  version: 1;
  conversations: Conversation[];
  activeId: string | null;
}

/** Reads saved conversations. Returns null when nothing valid is stored. */
export function loadState(): Omit<Stored, "version"> | null {
  try {
    const raw = localStorage.getItem(config.storageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Stored;
    if (parsed?.version !== 1 || !Array.isArray(parsed.conversations)) return null;
    // A turn still "pending" when the page closed never got its answer.
    const conversations = parsed.conversations.map((c) => ({
      ...c,
      turns: c.turns.map((t) =>
        t.status === "pending" ? { ...t, status: "error" as const, error: "The page was closed before SipGuide answered." } : t,
      ),
    }));
    return { conversations, activeId: parsed.activeId ?? null };
  } catch {
    return null;
  }
}

export function saveState(conversations: Conversation[], activeId: string | null): void {
  try {
    const data: Stored = { version: 1, conversations, activeId };
    localStorage.setItem(config.storageKey, JSON.stringify(data));
  } catch {
    // Storage full or blocked (private mode): the session keeps working in memory.
  }
}

export function clearState(): void {
  try {
    localStorage.removeItem(config.storageKey);
  } catch {
    /* ignore */
  }
}
