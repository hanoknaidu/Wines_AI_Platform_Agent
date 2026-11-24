import { describe, expect, it } from "vitest";
import {
  actionLabels,
  actionName,
  actionState,
  classifyReply,
  announcementFor,
  conversationStatus,
  isAffirmative,
  isNegative,
  outcomeOf,
  supportStatus,
  verdictOf,
} from "../lib/status";
import type { AgentMeta, Conversation, Turn } from "../types";

const NOW = Date.parse("2026-11-23T20:00:00Z");

function meta(partial: Partial<AgentMeta> = {}): AgentMeta {
  return {
    run_id: "run_x",
    status: "completed",
    intent: { name: "order.cancel", confidence: 0.9 },
    tools_used: [],
    kb_sources: [],
    pending_action: null,
    requires_confirmation: false,
    executed_action: null,
    escalation: null,
    llm_provider: "mock",
    duration_ms: 10,
    ...partial,
  };
}

function turn(m: AgentMeta, extra: Partial<Turn> = {}, content = "Your order **WA-1** can be cancelled. Want me to?"): Turn {
  return {
    id: "turn_1",
    human: { id: "msg_h", role: "human", content: "cancel", createdAt: "2026-11-23T19:59:00Z" },
    ai: { id: "msg_a", role: "ai", content, createdAt: "2026-11-23T20:00:00Z", meta: m },
    status: "complete",
    ...extra,
  };
}

const offer = (expiresInMs: number) =>
  meta({
    pending_action: {
      action_id: "act_1",
      tool: "cancel_order",
      summary: "Cancel order WA-1",
      expires_at: new Date(NOW + expiresInMs).toISOString(),
    },
    requires_confirmation: true,
  });

describe("actionState", () => {
  it("is open only on the latest turn before it expires", () => {
    expect(actionState(turn(offer(60_000)), true, NOW)).toBe("open");
    expect(actionState(turn(offer(60_000)), false, NOW)).toBe("closed");
    expect(actionState(turn(offer(-1)), true, NOW)).toBe("expired");
  });

  it("reports the customer's decision over everything else", () => {
    expect(actionState(turn(offer(-1), { actionDecision: "declined" }), true, NOW)).toBe("declined");
    expect(actionState(turn(meta()), true, NOW)).toBeNull();
  });
});

describe("verdictOf", () => {
  it("names hand-offs, open offers and completed actions; plain answers get none", () => {
    expect(verdictOf(turn(meta({ escalation: { ticket_number: "TKT-1", priority: null, reason_code: null } })), true, NOW)).toBe(
      "with_team",
    );
    expect(verdictOf(turn(offer(60_000)), true, NOW)).toBe("needs_you");
    const done = { action_id: "act_1", tool: "cancel_order", ok: true, references: {} };
    expect(verdictOf(turn(meta({ executed_action: done })), true, NOW)).toBe("resolved");
    expect(verdictOf(turn(meta({ executed_action: { ...done, ok: false } })), true, NOW)).toBeNull();
    expect(verdictOf(turn(meta()), true, NOW)).toBeNull();
  });
});

describe("typed answers to an offer", () => {
  it("accepts only unambiguous yes and no", () => {
    for (const yes of ["yes", "Yes please!", "go ahead", "OK.", "yes, go ahead"]) expect(isAffirmative(yes)).toBe(true);
    for (const no of ["no", "No thanks", "not now", "Don’t"]) expect(isNegative(no)).toBe(true);
    for (const other of ["yes but what about my other order?", "is it refundable", "no idea, what are my options"]) {
      expect(isAffirmative(other) || isNegative(other)).toBe(false);
    }
  });
});

describe("classifyReply", () => {
  it("needs an explicit yes for any action and holds a casual one", () => {
    expect(classifyReply("yes")).toBe("confirm");
    expect(classifyReply("Go ahead.")).toBe("confirm");
    expect(classifyReply("ok")).toBe("hold");
    expect(classifyReply("sure, what about my other order?")).toBe("hold");
    expect(classifyReply("no thanks")).toBe("decline");
    expect(classifyReply("when does the store open?")).toBe("other");
  });
});

describe("outcomeOf", () => {
  const exec = (tool: string, references: Record<string, string>, ok = true) =>
    turn(meta({ executed_action: { action_id: "act_1", tool, ok, references } }));

  it("builds a receipt from executed_action.references", () => {
    expect(outcomeOf(exec("create_return_request", { rma_number: "RMA-1", order_id: "WA-2" }))).toEqual({
      title: "Return started",
      ok: true,
      rows: [
        { label: "Return", value: "RMA-1" },
        { label: "Order", value: "WA-2" },
      ],
    });
    expect(outcomeOf(turn(meta()))).toBeNull();
  });

  it("restates the refund amount and reports failures", () => {
    const cancelled = outcomeOf(exec("cancel_order", { order_id: "WA-1", refund_id: "RF-1", amount: "104.50" }));
    expect(cancelled?.rows).toEqual([
      { label: "Order", value: "WA-1" },
      { label: "Refund", value: "$104.50" },
    ]);
    expect(outcomeOf(exec("cancel_order", {}, false))).toEqual({ title: "That didn't go through", ok: false, rows: [] });
  });
});

describe("conversationStatus", () => {
  it("flags an open offer and remembers the ticket", () => {
    const c: Conversation = {
      id: "conv_1",
      title: "t",
      createdAt: "",
      updatedAt: "",
      turns: [turn(meta({ escalation: { ticket_number: "TKT-9", priority: null, reason_code: null } })), { ...turn(offer(60_000)), id: "turn_2" }],
    };
    expect(conversationStatus(c, NOW)).toEqual({ needsYou: true, ticket: "TKT-9" });
  });
});

describe("supportStatus", () => {
  it("uses Eastern time support hours", () => {
    expect(supportStatus(new Date("2026-11-23T20:00:00Z")).online).toBe(true); // 3 pm ET
    expect(supportStatus(new Date("2026-11-24T03:00:00Z"))).toEqual({ online: false, label: "Team back at 9 am ET" }); // 10 pm ET
  });
});

describe("announcementFor", () => {
  it("reads the first sentence and says when an answer is needed", () => {
    expect(announcementFor(turn(offer(60_000)), NOW)).toBe(
      "SipGuide replied: Your order WA-1 can be cancelled. Your answer is needed: Cancel order WA-1.",
    );
  });
});

describe("actionName", () => {
  it("names the card in every state", () => {
    expect(actionName("create_return_request", "confirmed")).toBe("Return: you said yes");
    expect(actionName("cancel_order", "expired")).toBe("Cancellation: offer expired");
  });
});

describe("actionLabels", () => {
  it("names the outcome", () => {
    expect(actionLabels("cancel_order")).toEqual({ confirm: "Cancel order", decline: "Keep order" });
    expect(actionLabels("unknown").confirm).toBe("Go ahead");
  });
});
