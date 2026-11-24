import type { Conversation } from "../types";

export interface ConversationGroup {
  label: string;
  items: Conversation[];
}

const DAY = 24 * 60 * 60 * 1000;

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Groups conversations (newest activity first) into Today / Yesterday / Previous 7 days / Older. */
export function groupByRecency(conversations: Conversation[], now = new Date()): ConversationGroup[] {
  const today = startOfDay(now);
  const buckets: ConversationGroup[] = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Previous 7 days", items: [] },
    { label: "Older", items: [] },
  ];
  const sorted = [...conversations].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  for (const c of sorted) {
    const t = new Date(c.updatedAt).getTime();
    const index = t >= today ? 0 : t >= today - DAY ? 1 : t >= today - 7 * DAY ? 2 : 3;
    buckets[index].items.push(c);
  }
  return buckets.filter((b) => b.items.length > 0);
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}
