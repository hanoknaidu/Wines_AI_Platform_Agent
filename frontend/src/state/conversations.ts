import { titleFromMessage } from "../lib/title";
import type { ActionDecision, Conversation, Message, Turn } from "../types";

export interface ChatState {
  conversations: Conversation[];
  /** null = the "new conversation" screen. A conversation is only created when its first message is sent. */
  activeId: string | null;
}

export type ChatAction =
  | { type: "send"; conversationId: string; turn: Turn; now: string }
  | { type: "resolve"; conversationId: string; turnId: string; ai: Message; now: string }
  | { type: "fail"; conversationId: string; turnId: string; error: string }
  | { type: "retry"; conversationId: string; turnId: string }
  | { type: "stop"; conversationId: string; turnId: string }
  | { type: "requestReopen"; conversationId: string; turnId: string }
  | { type: "decideAction"; conversationId: string; turnId: string; decision: ActionDecision }
  | { type: "select"; conversationId: string | null }
  | { type: "delete"; conversationId: string }
  | { type: "clearAll" };

export const emptyState: ChatState = { conversations: [], activeId: null };

function updateConversation(state: ChatState, id: string, fn: (c: Conversation) => Conversation): ChatState {
  return { ...state, conversations: state.conversations.map((c) => (c.id === id ? fn(c) : c)) };
}

function updateTurn(c: Conversation, turnId: string, fn: (t: Turn) => Turn): Conversation {
  return { ...c, turns: c.turns.map((t) => (t.id === turnId ? fn(t) : t)) };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "send": {
      const existing = state.conversations.find((c) => c.id === action.conversationId);
      if (!existing) {
        const created: Conversation = {
          id: action.conversationId,
          title: titleFromMessage(action.turn.human.content),
          createdAt: action.now,
          updatedAt: action.now,
          turns: [action.turn],
        };
        return { conversations: [created, ...state.conversations], activeId: created.id };
      }
      return {
        ...updateConversation(state, existing.id, (c) => ({ ...c, turns: [...c.turns, action.turn], updatedAt: action.now })),
        activeId: existing.id,
      };
    }

    case "resolve":
      return updateConversation(state, action.conversationId, (c) => ({
        ...updateTurn(c, action.turnId, (t) => ({ ...t, ai: action.ai, status: "complete", error: undefined })),
        updatedAt: action.now,
      }));

    case "fail":
      return updateConversation(state, action.conversationId, (c) =>
        updateTurn(c, action.turnId, (t) => ({ ...t, status: "error", error: action.error })),
      );

    case "retry":
      return updateConversation(state, action.conversationId, (c) =>
        updateTurn(c, action.turnId, (t) => ({ ...t, status: "pending", error: undefined, stopped: undefined })),
      );

    case "stop":
      return updateConversation(state, action.conversationId, (c) =>
        updateTurn(c, action.turnId, (t) =>
          t.status === "pending" ? { ...t, status: "error", error: "You stopped this answer.", stopped: true } : t,
        ),
      );

    case "requestReopen":
      return updateConversation(state, action.conversationId, (c) =>
        updateTurn(c, action.turnId, (t) => ({ ...t, reopenRequested: true })),
      );

    case "decideAction":
      return updateConversation(state, action.conversationId, (c) =>
        updateTurn(c, action.turnId, (t) => ({ ...t, actionDecision: action.decision })),
      );

    case "select":
      return { ...state, activeId: action.conversationId };

    case "delete": {
      const conversations = state.conversations.filter((c) => c.id !== action.conversationId);
      return { conversations, activeId: state.activeId === action.conversationId ? null : state.activeId };
    }

    case "clearAll":
      return emptyState;
  }
}
