/**
 * What state a turn, its proposed action and its conversation are in, derived
 * from the agent's response metadata. Pure functions, so the byline, the
 * action card, the history markers and the screen-reader announcer all agree.
 */
import { config } from "../config";
import type { Conversation, Turn } from "../types";

// ---------------------------------------------------------------------------
// Proposed actions
// ---------------------------------------------------------------------------

/**
 * open      waiting for the customer (buttons shown)
 * confirmed / declined   the customer answered
 * closed    a later message moved on before the customer answered
 * expired   the agent's offer ran out (expires_at passed)
 */
export type ActionState = "open" | "confirmed" | "declined" | "closed" | "expired";

export function actionState(turn: Turn, isLatest: boolean, now: number = Date.now()): ActionState | null {
  const action = turn.ai?.meta?.pending_action;
  if (!action) return null;
  if (turn.actionDecision) return turn.actionDecision;
  if (Date.parse(action.expires_at) <= now) return "expired";
  return isLatest ? "open" : "closed";
}

/** Button labels that name the outcome instead of a generic "Confirm". */
export function actionLabels(tool: string): { confirm: string; decline: string } {
  switch (tool) {
    case "cancel_order":
      return { confirm: "Cancel order", decline: "Keep order" };
    case "create_return_request":
      return { confirm: "Start return", decline: "Not now" };
    case "request_refund":
      return { confirm: "Request refund", decline: "Not now" };
    default:
      return { confirm: "Go ahead", decline: "Not now" };
  }
}

/** The open action on the conversation's latest turn, if the customer still has to answer one. */
export function openActionTurn(conversation: Conversation | null, now: number = Date.now()): Turn | null {
  const last = conversation?.turns[conversation.turns.length - 1];
  if (!last || last.status !== "complete") return null;
  return actionState(last, true, now) === "open" ? last : null;
}

const YES = /^(yes|yeah|yep|yup|sure|ok|okay|confirm|confirmed|go ahead|do it|please do|please go ahead|yes please|yes go ahead|yes please go ahead|sounds good)$/;
/** Every action that changes an order needs an explicit yes. */
const STRICT_YES = /^(yes|yes please|go ahead|please go ahead|yes go ahead|yes please go ahead)$/;
/**
 * Mirrors AFFIRM_RE in app/agent/intent.py: the backend confirms on any message
 * that merely starts with one of these words. Used to stop a casual "ok, but…"
 * from reaching it while an irreversible offer is open.
 */
const BACKEND_AFFIRM = /^\s*(yes|yeah|yep|yup|sure|ok(ay)?|confirm(ed)?|go ahead|do it|please do|correct|that'?s (right|fine|correct)|sounds good|approved?)\b/i;

/** Message the UI sends when the customer asks the team to reopen a closed or expired offer. */
export const REOPEN_PREFIX = "Please ask the team to review reopening this offer:";
const NO = /^(no|nope|not now|no thanks|no thank you|not now thanks|not now thank you|don't|do not|never mind|nevermind)$/;

function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[.,!]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** An unambiguous typed "yes" to an open offer (the backend accepts the same). */
export const isAffirmative = (text: string) => YES.test(normalize(text));
/** An unambiguous typed "no". */
export const isNegative = (text: string) => NO.test(normalize(text));

/**
 * What a typed message does to an open offer: confirm / decline it, "hold" (a
 * casual "ok" or "sure, …": ask for an explicit yes instead of sending, since the
 * backend would treat it as consent), or "other" (a new question; the offer closes).
 */
export function classifyReply(text: string): "confirm" | "decline" | "hold" | "other" {
  const n = normalize(text);
  if (NO.test(n)) return "decline";
  if (STRICT_YES.test(n)) return "confirm";
  return BACKEND_AFFIRM.test(text) && !/\b(no|not|don'?t)\b/i.test(text) ? "hold" : "other";
}

const ACTION_NOUNS: Record<string, string> = {
  cancel_order: "Cancellation",
  create_return_request: "Return",
  request_refund: "Refund",
};

const STATE_PHRASES: Record<ActionState, string> = {
  open: "your answer is needed",
  confirmed: "you said yes",
  declined: "you said no",
  closed: "offer closed",
  expired: "offer expired",
};

/** Accessible name for the action card, in every state ("Return: you said yes"). */
export function actionName(tool: string, state: ActionState): string {
  return `${ACTION_NOUNS[tool] ?? "Offer"}: ${STATE_PHRASES[state]}`;
}

// ---------------------------------------------------------------------------
// Turn verdict (the status byline)
// ---------------------------------------------------------------------------

export type Verdict = "needs_you" | "resolved" | "with_team";

export const VERDICT_LABELS: Record<Verdict, string> = {
  needs_you: "Needs you",
  resolved: "Resolved",
  with_team: "With our team",
};

/** Only answers that changed something, wait on the customer or handed off get a verdict. */
export function verdictOf(turn: Turn, isLatest: boolean, now: number = Date.now()): Verdict | null {
  const meta = turn.ai?.meta;
  if (turn.status !== "complete" || !meta) return null;
  if (meta.escalation) return "with_team";
  if (actionState(turn, isLatest, now) === "open") return "needs_you";
  if (meta.executed_action && meta.executed_action.ok !== false) return "resolved";
  return null;
}

// ---------------------------------------------------------------------------
// Outcomes (receipt under an answer that did something)
// ---------------------------------------------------------------------------

export interface Outcome {
  title: string;
  ok: boolean;
  rows: { label: string; value: string }[];
}

const OUTCOME_TITLES: Record<string, string> = {
  cancel_order: "Order cancelled",
  create_return_request: "Return started",
  request_refund: "Refund requested",
};

/** Keys of executed_action.references (app/agent/service.py _executed_out). */
const OUTCOME_FIELDS: [key: string, label: string][] = [
  ["rma_number", "Return"],
  ["order_id", "Order"],
  ["refund_id", "Refund"],
  ["amount", "Refund"],
];

function formatAmount(value: unknown): string {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n) : String(value);
}

export function outcomeOf(turn: Turn): Outcome | null {
  const meta = turn.ai?.meta;
  if (!meta) return null;
  // Hand-offs have no receipt: the ticket panel is their one home.
  if (meta.escalation) return null;
  const done = meta.executed_action;
  if (!done) return null;
  const tool = done.tool;
  if (done.ok === false) return { title: "That didn't go through", ok: false, rows: [] };
  const refs: Record<string, unknown> = done.references ?? {};
  const rows = OUTCOME_FIELDS.flatMap(([key, label]) => {
    const v = refs[key];
    if (typeof v !== "string" && typeof v !== "number") return [];
    return [{ label, value: key === "amount" ? formatAmount(v) : String(v) }];
  });
  // A refund ID and its amount share the "Refund" label: keep the amount.
  const unique = rows.filter((r, i) => !(r.label === "Refund" && rows.slice(i + 1).some((x) => x.label === "Refund")));
  return { title: OUTCOME_TITLES[tool] ?? "Done", ok: true, rows: unique };
}

// ---------------------------------------------------------------------------
// Conversation-level status (history markers, hand-off strip)
// ---------------------------------------------------------------------------

/** Prefix of a customer note added to an open ticket from the prompt bar. */
export const notePrefix = (ticket: string) => `For ticket ${ticket}:`;

export interface TicketInfo {
  number: string;
  kind: "person" | "review";
  /** What the customer asked for, in their terms. */
  about: string;
}

/** One entry per ticket opened in a conversation, oldest first. */
export function conversationTickets(conversation: Conversation): TicketInfo[] {
  const tickets: TicketInfo[] = [];
  for (const t of conversation.turns) {
    const esc = t.ai?.meta?.escalation;
    if (!esc?.ticket_number || tickets.some((x) => x.number === esc.ticket_number)) continue;
    if (esc.reason_code === "offer_reopen_review") {
      const offer = t.human.content.slice(REOPEN_PREFIX.length).trim().replace(/\.$/, "");
      const what = offer.replace(/^Start a /, "").replace(/^(\w)/, (c) => c.toLowerCase());
      tickets.push({ number: esc.ticket_number, kind: "review", about: `Review to reopen: ${what}` });
    } else {
      tickets.push({ number: esc.ticket_number, kind: "person", about: "Request for a person" });
    }
  }
  return tickets;
}

export function conversationStatus(conversation: Conversation, now: number = Date.now()) {
  let ticket: string | null = null;
  for (const t of conversation.turns) ticket = t.ai?.meta?.escalation?.ticket_number ?? ticket;
  return { needsYou: openActionTurn(conversation, now) !== null, ticket };
}

/** Human support hours (business profile: 9:00 am – 9:00 pm ET, 7 days). */
export function supportStatus(now: Date = new Date()): { online: boolean; label: string } {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: config.supportHours.timeZone,
    hour: "numeric",
    minute: "numeric",
    hourCycle: "h23",
  }).formatToParts(now);
  const hour = Number(parts.find((p) => p.type === "hour")?.value ?? 0);
  const minute = Number(parts.find((p) => p.type === "minute")?.value ?? 0);
  const h = hour + minute / 60;
  const { open, close } = config.supportHours;
  const fmt = (x: number) => `${x % 12 === 0 ? 12 : x % 12} ${x < 12 ? "am" : "pm"} ET`;
  return h >= open && h < close
    ? { online: true, label: `Team online until ${fmt(close)}` }
    : { online: false, label: `Team back at ${fmt(open)}` };
}

// ---------------------------------------------------------------------------
// Screen-reader announcement for the newest turn
// ---------------------------------------------------------------------------

function plain(text: string): string {
  return text.replace(/\*\*/g, "").replace(/^- /gm, "").replace(/\s+/g, " ").trim();
}

function firstSentence(text: string): string {
  const flat = plain(text);
  const match = flat.match(/^.+?[.!?](?=\s|$)/);
  return match ? match[0] : flat;
}

export function announcementFor(turn: Turn, now: number = Date.now()): string {
  if (turn.status === "pending") return "SipGuide is checking.";
  if (turn.status === "error") return turn.stopped ? "Answer stopped." : "That answer didn't come through. You can try again.";
  const ai = turn.ai;
  if (!ai) return "";
  let text = `SipGuide replied: ${firstSentence(ai.content)}`;
  const action = ai.meta?.pending_action;
  if (action && actionState(turn, true, now) === "open") text += ` Your answer is needed: ${action.summary}.`;
  if (ai.meta?.escalation?.ticket_number) text += ` Ticket ${ai.meta.escalation.ticket_number} is open with our team.`;
  return text;
}
