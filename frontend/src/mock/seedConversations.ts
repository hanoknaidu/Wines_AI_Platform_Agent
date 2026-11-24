/**
 * Sample history shown on first load, so the sidebar is not empty.
 * Built through the same model as live conversations (fresh IDs each time).
 * Content uses the fictional seed data in _DB/.
 */
import { hex32, newConversationId, newMessageId, newTurnId } from "../lib/ids";
import { titleFromMessage } from "../lib/title";
import type { AgentMeta, Conversation, Turn } from "../types";

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

function meta(partial: Partial<AgentMeta> & Pick<AgentMeta, "intent">): AgentMeta {
  return {
    run_id: `run_${hex32()}`,
    status: "completed",
    tools_used: [],
    kb_sources: [],
    pending_action: null,
    requires_confirmation: false,
    executed_action: null,
    escalation: null,
    llm_provider: "mock",
    duration_ms: 1100,
    ...partial,
  };
}

function turn(at: number, question: string, answer: string, agentMeta: AgentMeta): Turn {
  return {
    id: newTurnId(),
    human: { id: newMessageId(), role: "human", content: question, createdAt: new Date(at).toISOString() },
    ai: { id: newMessageId(), role: "ai", content: answer, createdAt: new Date(at + 2000).toISOString(), meta: agentMeta },
    status: "complete",
  };
}

function conversation(turns: Turn[]): Conversation {
  return {
    id: newConversationId(),
    title: titleFromMessage(turns[0].human.content),
    createdAt: turns[0].human.createdAt,
    updatedAt: turns[turns.length - 1].ai!.createdAt,
    turns,
  };
}

export function seedConversations(now = Date.now()): Conversation[] {
  const yesterday = now - DAY - 2 * HOUR;
  const lastWeek = now - 4 * DAY;

  return [
    conversation([
      turn(
        yesterday,
        "Do you deliver to Philadelphia?",
        "I'm sorry, we can't deliver to Pennsylvania. We deliver and ship to addresses in **New Jersey and New York only**, and each order goes out from the licensed store in that state.\n\nIf you have an NJ or NY address, such as a friend's or your office, I'm happy to help you send it there.",
        meta({
          intent: { name: "compliance.out_of_state", confidence: 0.96 },
          kb_sources: [{ id: "KB-ORD-007", title: "In-State Shipping Policy (NJ and NY Only)", section: "Where we ship" }],
        }),
      ),
      turn(
        yesterday + 3 * 60 * 1000,
        "What about Jersey City?",
        "Yes, Jersey City is in New Jersey, so it's covered by our **NJ Store (Hoboken)**. You can choose local delivery or pick up in store at checkout.",
        meta({
          intent: { name: "delivery.eligibility", confidence: 0.92 },
          kb_sources: [{ id: "KB-ORD-004", title: "Local Delivery Policy", section: "Service area" }],
        }),
      ),
    ]),
    conversation([
      turn(
        lastWeek,
        "Which sparkling wines do you have without alcohol?",
        "We carry **Clearleaf Zero Sparkling Rosé** ($18): bright strawberry and a fine, lively fizz. It's the one customers pick most often for toasts when someone isn't drinking.\n\nOne note: all our products, including non-alcoholic wines, are sold only to customers 21 and older.",
        meta({
          intent: { name: "recommend.non_alcoholic", confidence: 0.94 },
          tools_used: ["search_products"],
          kb_sources: [
            { id: "KB-NAW-003", title: "Non-Alcoholic Wine Recommendations by Occasion and FAQ", section: "Toasts" },
            { id: "KB-NAW-002", title: "Non-Alcoholic Wine Sale Policy, Age Rules and Sensitive Situations", section: "Age rules" },
          ],
        }),
      ),
    ]),
  ];
}
