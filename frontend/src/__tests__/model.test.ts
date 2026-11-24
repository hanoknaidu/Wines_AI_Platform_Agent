import { describe, expect, it } from "vitest";
import { buildAgentContext } from "../lib/context";
import { groupByRecency } from "../lib/dates";
import { newConversationId, newMessageId, newTurnId } from "../lib/ids";
import { titleFromMessage } from "../lib/title";
import { mockChat } from "../mock/mockAgent";
import { seedConversations } from "../mock/seedConversations";
import { chatReducer, emptyState } from "../state/conversations";
import type { Conversation, Turn } from "../types";

const SESSION_ID_PATTERN = /^[A-Za-z0-9_-]{4,100}$/;

function makeTurn(content: string, status: Turn["status"] = "pending"): Turn {
  const now = new Date().toISOString();
  return {
    id: newTurnId(),
    human: { id: newMessageId(), role: "human", content, createdAt: now },
    ai: status === "complete" ? { id: newMessageId(), role: "ai", content: `Answer to: ${content}`, createdAt: now } : null,
    status,
  };
}

describe("ids", () => {
  it("are unique, prefixed, and conversation IDs pass the backend session_id pattern", () => {
    const ids = new Set(Array.from({ length: 500 }, newConversationId));
    expect(ids.size).toBe(500);
    for (const id of ids) expect(id).toMatch(SESSION_ID_PATTERN);
    expect(newMessageId()).toMatch(/^msg_[0-9a-f]{32}$/);
    expect(newTurnId()).toMatch(/^turn_[0-9a-f]{32}$/);
  });
});

describe("titleFromMessage", () => {
  it("uses the first question, trimmed and capitalized", () => {
    expect(titleFromMessage("  where is my   order??  ")).toBe("Where is my order");
  });
  it("drops a leading greeting", () => {
    expect(titleFromMessage("Hi! Can I return a bottle?")).toBe("Can I return a bottle");
  });
  it("keeps a greeting-only message", () => {
    expect(titleFromMessage("hello")).toBe("Hello");
  });
  it("cuts long questions at a word boundary", () => {
    const title = titleFromMessage(
      "I ordered two bottles of Sancerre last week and one of them arrived with a broken cork, what can I do",
    );
    expect(title.length).toBeLessThanOrEqual(49);
    expect(title.endsWith("…")).toBe(true);
    expect(title).not.toMatch(/\s…$/);
  });
  it("falls back for empty input", () => {
    expect(titleFromMessage("   ?? ")).toBe("New conversation");
  });
});

describe("chatReducer", () => {
  it("creates a conversation on the first message, titled from it", () => {
    const id = newConversationId();
    const turn = makeTurn("Where is my latest order?");
    const state = chatReducer(emptyState, { type: "send", conversationId: id, turn, now: turn.human.createdAt });
    expect(state.activeId).toBe(id);
    expect(state.conversations).toHaveLength(1);
    expect(state.conversations[0].title).toBe("Where is my latest order");
    expect(state.conversations[0].turns).toEqual([turn]);
  });

  it("appends turns in order and keeps the title", () => {
    const id = newConversationId();
    const t1 = makeTurn("First question");
    const t2 = makeTurn("Second question");
    let state = chatReducer(emptyState, { type: "send", conversationId: id, turn: t1, now: "2026-11-23T10:00:00Z" });
    state = chatReducer(state, { type: "send", conversationId: id, turn: t2, now: "2026-11-23T10:01:00Z" });
    const c = state.conversations[0];
    expect(c.title).toBe("First question");
    expect(c.turns.map((t) => t.id)).toEqual([t1.id, t2.id]);
    expect(c.updatedAt).toBe("2026-11-23T10:01:00Z");
  });

  it("resolves, fails and retries a turn", () => {
    const id = newConversationId();
    const turn = makeTurn("Question");
    let state = chatReducer(emptyState, { type: "send", conversationId: id, turn, now: "2026-11-23T10:00:00Z" });
    state = chatReducer(state, { type: "fail", conversationId: id, turnId: turn.id, error: "Network" });
    expect(state.conversations[0].turns[0]).toMatchObject({ status: "error", error: "Network" });
    state = chatReducer(state, { type: "retry", conversationId: id, turnId: turn.id });
    expect(state.conversations[0].turns[0].status).toBe("pending");
    const ai = { id: newMessageId(), role: "ai" as const, content: "Answer", createdAt: "2026-11-23T10:00:02Z" };
    state = chatReducer(state, { type: "resolve", conversationId: id, turnId: turn.id, ai, now: ai.createdAt });
    expect(state.conversations[0].turns[0]).toMatchObject({ status: "complete", ai, error: undefined });
  });

  it("deleting the active conversation returns to the new-conversation screen", () => {
    const id = newConversationId();
    let state = chatReducer(emptyState, { type: "send", conversationId: id, turn: makeTurn("Q"), now: "2026-11-23T10:00:00Z" });
    state = chatReducer(state, { type: "delete", conversationId: id });
    expect(state).toEqual(emptyState);
  });
});

describe("buildAgentContext", () => {
  const conversation: Conversation = {
    id: newConversationId(),
    title: "t",
    createdAt: "",
    updatedAt: "",
    turns: [makeTurn("one", "complete"), makeTurn("two", "error"), makeTurn("three", "complete"), makeTurn("four")],
  };

  it("passes completed turns in order, each message with its own ID", () => {
    const context = buildAgentContext(conversation, 10);
    expect(context.map((m) => [m.role, m.content])).toEqual([
      ["user", "one"],
      ["assistant", "Answer to: one"],
      ["user", "three"],
      ["assistant", "Answer to: three"],
    ]);
    expect(context[0].message_id).toBe(conversation.turns[0].human.id);
    expect(context[1].message_id).toBe(conversation.turns[0].ai!.id);
  });

  it("keeps only the most recent turns", () => {
    expect(buildAgentContext(conversation, 1).map((m) => m.content)).toEqual(["three", "Answer to: three"]);
  });
});

describe("groupByRecency", () => {
  it("groups newest first", () => {
    const now = new Date("2026-11-23T15:00:00");
    const seeds = seedConversations(now.getTime());
    const groups = groupByRecency(seeds, now);
    expect(groups.map((g) => g.label)).toEqual(["Yesterday", "Previous 7 days"]);
  });
});

describe("mockChat", () => {
  const base = { customer_id: "C-100005", session_id: newConversationId(), confirm_action_id: null, channel: "web_chat" as const };

  it("returns the backend ChatResponse shape", async () => {
    const res = await mockChat({ ...base, message: "Where is my latest order?" }, []);
    expect(res).toMatchObject({ session_id: base.session_id, status: "completed", requires_confirmation: false });
    expect(res.run_id).toMatch(/^run_[0-9a-f]{32}$/);
    expect(res.intent?.name).toBe("order.status");
    expect(res.kb_sources.length).toBeGreaterThan(0);
  });

  it("collects order details and checks the policy before offering a return", async () => {
    const ask = await mockChat({ ...base, message: "I want to return a bottle" }, []);
    expect(ask.requires_confirmation).toBe(false);
    expect(ask.message).toContain("Order number");
    const history = [
      { message_id: "msg_1", role: "user" as const, content: "I want to return a bottle" },
      { message_id: "msg_2", role: "assistant" as const, content: ask.message },
    ];
    const notEligible = await mockChat({ ...base, message: "WA-100105" }, history);
    expect(notEligible.requires_confirmation).toBe(false);
    const which = await mockChat({ ...base, message: "It's order WA-100114" }, history);
    expect(which.requires_confirmation).toBe(false);
    expect(which.message).toContain("Which bottle");
  });

  it("proposes an action that needs confirmation, then executes it", async () => {
    const proposed = await mockChat({ ...base, message: "Return the unopened rosé from WA-100114" }, []);
    expect(proposed.requires_confirmation).toBe(true);
    expect(proposed.pending_action?.action_id).toMatch(/^act_[0-9a-f]{32}$/);
    const done = await mockChat(
      { ...base, message: "Yes, go ahead", confirm_action_id: proposed.pending_action!.action_id },
      [],
    );
    expect(done.executed_action).not.toBeNull();
    expect(done.requires_confirmation).toBe(false);
  });

  it("uses earlier turns for an unclear follow-up", async () => {
    const res = await mockChat({ ...base, message: "hmm ok" }, [
      { message_id: "msg_1", role: "user", content: "Is the Barolo in stock?" },
      { message_id: "msg_2", role: "assistant", content: "Let me check." },
    ]);
    expect(res.message).toContain("Is the Barolo in stock");
  });

  it("can simulate a failure", async () => {
    await expect(mockChat({ ...base, message: "simulate error" }, [])).rejects.toThrow();
  });
});
