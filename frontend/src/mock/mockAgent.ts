/**
 * Phase 1 stand-in for POST /api/v1/agent/chat.
 *
 * Keyword rules pick a canned answer and return it in the exact ChatResponse
 * shape. Order numbers, products and prices come from the fictional seed data
 * in _DB/ (customer C-100005); KB sources are real _KB/ document IDs. Nothing
 * here quotes a fee, threshold or time window: those are A-xx assumptions that
 * only live tools may state.
 *
 * Special inputs for testing UI states:
 *   "simulate error"  → the request fails (error + retry state)
 *   "simulate slow"   → a 6-second response (pending state)
 */
import { hex32 } from "../lib/ids";
import { REOPEN_PREFIX } from "../lib/status";
import type { ChatRequest, ChatResponse, ContextMessage, ExecutedActionOut, KbSource, PendingActionOut } from "../types";

interface Reply {
  message: string;
  intent: string;
  confidence: number;
  tools: string[];
  sources: KbSource[];
  pendingAction?: Omit<PendingActionOut, "action_id" | "expires_at">;
  executedAction?: Omit<ExecutedActionOut, "action_id">;
  escalation?: ChatResponse["escalation"];
}

const KB = {
  orderStatus: { id: "KB-ORD-002", title: "Order Status Lifecycle", section: "Ready for pickup" },
  pickup: { id: "KB-ORD-005", title: "In-Store and Curbside Pickup Policy", section: "What to bring" },
  cancellations: { id: "KB-ORD-003", title: "Order Changes and Cancellations", section: "Before handoff" },
  localDelivery: { id: "KB-ORD-004", title: "Local Delivery Policy", section: "Service area" },
  shipping: { id: "KB-ORD-007", title: "In-State Shipping Policy (NJ and NY Only)", section: "Where we ship" },
  returns: { id: "KB-RTN-001", title: "Returns Policy (Master Policy and Decision Tree)", section: "Eligibility" },
  refunds: { id: "KB-RTN-005", title: "Refunds and Store Credit", section: "How refunds are issued" },
  damaged: { id: "KB-RTN-002", title: "Damaged or Broken Items on Delivery", section: "Reporting a claim" },
  flawed: { id: "KB-RTN-003", title: "Corked or Flawed Wine (Fault Identification and Claims)", section: "Signs of a fault" },
  boldReds: { id: "KB-TST-009", title: "Bold & Full-Bodied Red Wines", section: "Crowd-pleasers" },
  pairing: { id: "KB-TST-011", title: "Food and Wine Pairing Guide", section: "Red meat" },
  escalation: { id: "KB-SYS-006", title: "Escalation Matrix and Human Handoff Procedure", section: "Customer-requested handoff" },
} satisfies Record<string, KbSource>;

const has = (text: string, ...words: string[]) => words.some((w) => text.includes(w));

/** Tool behind each action ID this mock proposed (in memory; forgotten on reload). */
const issuedActions = new Map<string, { tool: string; summary: string }>();


const lastAssistant = (context: ContextMessage[]) => [...context].reverse().find((m) => m.role === "assistant")?.content ?? "";
const openTicket = (context: ContextMessage[]) =>
  context.filter((m) => m.role === "assistant").map((m) => m.content.match(/ticket \*\*(TKT-\d+)\*\*/)?.[1]).filter(Boolean).pop() ?? null;

/** The customer's previous request, described in plain words (never a cut-off system string). */
function lastAssistantTopic(context: ContextMessage[]): string | null {
  const lastUser = [...context].reverse().find((m) => m.role === "user");
  if (!lastUser) return null;
  const text = lastUser.content.trim();
  if (text.startsWith(REOPEN_PREFIX)) return "your request to have our team reopen that offer";
  if (/^For ticket TKT-\d+:/.test(text)) return "the note you added to your ticket";
  if (/^Yes, go ahead:/.test(text)) return "the action you just confirmed";
  if (text.length <= 60) return `“${text.replace(/[.?!]+$/, "")}”`;
  const cut = text.slice(0, 60);
  return `“${cut.slice(0, cut.lastIndexOf(" ")).replace(/[,;:]$/, "")}…”`;
}

function replyFor(request: ChatRequest, context: ContextMessage[]): Reply {
  const text = request.message.toLowerCase();

  // A confirmed action from an earlier turn.
  if (request.confirm_action_id) {
    const issued = issuedActions.get(request.confirm_action_id);
    const tool = issued?.tool;
    if (tool === "cancel_order" || (!tool && has(text, "cancel"))) {
      return {
        message:
          "Done. Order **WA-100105** is cancelled, and the **$104.50** you paid goes back to the card you used. You'll get a confirmation email shortly.",
        intent: "order.cancel",
        confidence: 0.99,
        tools: ["cancel_order"],
        sources: [KB.cancellations, KB.refunds],
        executedAction: {
          tool: "cancel_order",
          ok: true,
          references: { order_id: "WA-100105", status: "cancelled", refund_id: "RF-400008", amount: "104.50" },
        },
      };
    }
    return {
      message:
        `I've started return **RMA-100031** for ${issued?.summary.match(/for (.+?) \(/)?.[1] ?? "your bottles"} from order **WA-100114**. We'll email you the next steps, and the refund goes to your original payment method once the return is received.`,
      intent: "return.change_of_mind",
      confidence: 0.99,
      tools: ["create_return_request"],
      sources: [KB.returns, KB.refunds],
      executedAction: { tool: "create_return_request", ok: true, references: { rma_number: "RMA-100031", order_id: "WA-100114" } },
    };
  }

  if (/^(no\b|not now|don't|do not)/.test(text.trim())) {
    return {
      message: "No problem. I haven't changed anything. Is there something else I can help with?",
      intent: "domain.action",
      confidence: 0.9,
      tools: [],
      sources: [],
    };
  }

  if (request.message.startsWith(REOPEN_PREFIX)) {
    return {
      message:
        "I've sent this to our team for review as ticket **TKT-100215**. They'll check whether the offer can be reopened and whether it's still within the policy period. Nothing changes until they approve it, and they'll reply by email.",
      intent: "human.review",
      confidence: 0.98,
      tools: ["create_support_ticket"],
      sources: [KB.escalation, KB.returns],
      escalation: { ticket_number: "TKT-100215", priority: "P3", reason_code: "offer_reopen_review" },
    };
  }

  const note = request.message.match(/^For ticket (TKT-\d+):/);
  if (note) {
    return {
      message: `I've added your note to ticket **${note[1]}**. Our team will see it with the rest of the conversation and reply by email.`,
      intent: "human.followup",
      confidence: 0.98,
      tools: ["add_ticket_message"],
      sources: [],
      escalation: { ticket_number: note[1], priority: "normal", reason_code: "customer_followup" },
    };
  }

  const existing = openTicket(context);
  if (existing && has(text, "human", "person", "representative", "agent please", "speak to someone", "talk to someone")) {
    return {
      message: `Your ticket **${existing}** is already with our team, so I've added this message to it rather than opening a new one. They'll reply by email.`,
      intent: "human.request",
      confidence: 0.95,
      tools: ["add_ticket_message"],
      sources: [KB.escalation],
      escalation: { ticket_number: existing, priority: "normal", reason_code: "customer_followup" },
    };
  }

  if (has(text, "human", "person", "representative", "agent please", "speak to someone", "talk to someone")) {
    return {
      message:
        "Of course. I've opened ticket **TKT-100214** and passed along this conversation so you won't have to repeat yourself. Our support team works **9:00 am – 9:00 pm ET, 7 days a week**, and someone will reply by email.",
      intent: "human.request",
      confidence: 0.97,
      tools: ["create_support_ticket"],
      sources: [KB.escalation],
      escalation: { ticket_number: "TKT-100214", priority: "normal", reason_code: "customer_requested" },
    };
  }

  if (has(text, "cancel")) {
    return {
      message:
        "Your most recent order, **WA-100105**, is ready for pickup at the NJ Store (Hoboken) and hasn't been collected yet, so it can still be cancelled.\n\nCancelling releases all 6 bottles and refunds **$104.50** to your original card. Do you want me to go ahead?",
      intent: "order.cancel",
      confidence: 0.93,
      tools: ["list_customer_orders", "get_order", "check_eligibility"],
      sources: [KB.cancellations],
      pendingAction: { tool: "cancel_order", summary: "Cancel order WA-100105 and refund $104.50 to the original card" },
    };
  }

  if (has(text, "broken", "damaged", "leak", "cracked", "corked", "smells", "tastes off", "flawed", "wrong item", "missing")) {
    const flawed = has(text, "corked", "smells", "tastes off", "flawed");
    return {
      message: flawed
        ? "I'm sorry, that's disappointing. A corked bottle usually smells musty, like wet cardboard, and the fruit tastes flat.\n\nWhich bottle was it, and from which order? Please keep the bottle and cork. If a photo is needed, I'll send you a secure upload link by email (we don't take files in chat)."
        : "I'm sorry your order arrived like that. Let's get it sorted.\n\nWhich order and which bottle was affected? If a photo of the damage is needed, I'll send you a secure upload link by email (we don't take files in chat).",
      intent: flawed ? "claim.flawed_wine" : "claim.damaged",
      confidence: 0.9,
      tools: ["list_customer_orders"],
      sources: [flawed ? KB.flawed : KB.damaged],
    };
  }

  // Returns: collect the order and bottle, check the policy, and only then offer.
  const inReturnThread = /\breturn/i.test(lastAssistant(context));
  const orderIn = (t: string) => t.match(/\bWA-?\d{6}\b/i)?.[0].toUpperCase().replace(/^WA-?/, "WA-") ?? null;
  // Remember the order number given earlier in the same return conversation.
  const orderNo =
    orderIn(request.message) ??
    (inReturnThread ? orderIn([...context].reverse().find((m) => m.role === "user" && orderIn(m.content))?.content ?? "") : null);
  if (has(text, "refund", "return", "send back", "money back") || (inReturnThread && (orderNo || has(text, "rosé", "rose", "sancerre", "opened", "unopened")))) {
    if (!orderNo) {
      return {
        message:
          "I can help with that. To check it against our Returns Policy, I need a few details:\n\n- **Order number** (it starts with WA-, for example WA-100114)\n- **Which bottle** you'd like to return\n- **Its condition**: is it unopened, with the capsule sealed and the label intact?\n\nIf the bottle arrived damaged or tastes off, tell me that instead, as it's handled as a claim.",
        intent: "return.collect_details",
        confidence: 0.9,
        tools: [],
        sources: [KB.returns],
      };
    }
    if (orderNo === "WA-100105") {
      return {
        message:
          "Order **WA-100105** hasn't been collected yet (it's ready for pickup at the NJ Store), so it can't be returned. It can still be **cancelled** for a full refund instead. Would you like that?",
        intent: "return.not_eligible",
        confidence: 0.92,
        tools: ["get_order", "check_eligibility"],
        sources: [KB.returns, KB.cancellations],
      };
    }
    if (orderNo !== "WA-100114") {
      return {
        message: `I couldn't find order **${orderNo}** on your account. Could you check the number? It's in your confirmation email.`,
        intent: "return.collect_details",
        confidence: 0.85,
        tools: ["list_customer_orders"],
        sources: [],
      };
    }
    if (has(text, "opened", "drank", "tasted") && !has(text, "unopened")) {
      return {
        message:
          "Thanks for checking. Under our Returns Policy, an **opened** bottle can't be returned for a change of mind. If it tasted off or was faulty, that's a claim and we can help: tell me what was wrong with it.",
        intent: "return.not_eligible",
        confidence: 0.88,
        tools: ["get_order", "check_eligibility"],
        sources: [KB.returns, KB.flawed],
      };
    }
    const rose = has(text, "rosé", "rose");
    const sancerre = has(text, "sancerre");
    if (!rose && !sancerre) {
      return {
        message:
          "I checked order **WA-100114** (delivered Nov 14) against our Returns Policy. These bottles are eligible if they're unopened:\n\n- 2 × Chateau Sainte-Lumiere Côtes de Provence Rosé 2025 — **$46.92**\n- 1 × Domaine des Trois Collines Sancerre 2024 — **$36.26**\n\nWhich bottle would you like to return?",
        intent: "return.eligibility",
        confidence: 0.9,
        tools: ["get_order", "check_eligibility"],
        sources: [KB.returns, KB.refunds],
      };
    }
    const item = rose
      ? { name: "2 × Chateau Sainte-Lumiere Côtes de Provence Rosé", price: "$46.92" }
      : { name: "1 × Domaine des Trois Collines Sancerre", price: "$36.26" };
    return {
      message: `I checked order **WA-100114** against our Returns Policy: it was delivered on Nov 14, it's within the return window, and unopened bottles qualify. So **${item.name}** (${item.price}) is eligible.\n\nWould you like me to start the return? The refund goes to your original payment method once we receive the bottle${rose ? "s" : ""}.`,
      intent: "return.change_of_mind",
      confidence: 0.93,
      tools: ["get_order", "check_eligibility"],
      sources: [KB.returns, KB.refunds],
      pendingAction: { tool: "create_return_request", summary: `Start a return for ${item.name} (order WA-100114)` },
    };
  }

  if (has(text, "where is", "order status", "my order", "track", "pickup", "pick up", "ready")) {
    return {
      message:
        "Good news, Aisha: order **WA-100105** is **ready for pickup** at the NJ Store (Hoboken).\n\n- 2 × Clearleaf Zero Sparkling Rosé\n- 2 × Clearleaf Zero Riesling\n- 2 × Thin Line Sauvignon Blanc 2025\n\nBring a valid photo ID. Whoever collects the order must be 21 or older, even for non-alcoholic bottles.",
      intent: "order.status",
      confidence: 0.95,
      tools: ["list_customer_orders", "get_order"],
      sources: [KB.orderStatus, KB.pickup],
    };
  }

  if (has(text, "deliver", "ship", "zip", "out of state", "pennsylvania", "connecticut", "california")) {
    return {
      message:
        "We deliver and ship to addresses in **New Jersey and New York only**. Orders go out from the licensed store in your state, so NJ addresses are served by our NJ Store and NY addresses by our NY Store.\n\nIf you share your ZIP code, I can check which delivery options are available there.",
      intent: "delivery.eligibility",
      confidence: 0.88,
      tools: [],
      sources: [KB.localDelivery, KB.shipping],
    };
  }

  if (has(text, "recommend", "suggest", "red", "white", "wine for", "pair", "steak", "dinner", "bottle", "gift")) {
    return {
      message:
        "Here are three bold reds that work well with a steak dinner, from everyday to special occasion:\n\n- **Altos del Viento Malbec** — $14. Plush dark fruit and soft tannins; an easy crowd-pleaser.\n- **Galil Heights Cabernet Sauvignon** — $27. Blackcurrant and cedar, with structure to stand up to grilled meat.\n- **Hollow Creek Cellars Napa Valley Cabernet Sauvignon** — $48. Rich, ripe and polished; a great pick for a celebration.\n\nWould you like me to check which of these your Hoboken store has in stock?",
      intent: "recommend.by_food",
      confidence: 0.86,
      tools: ["search_products"],
      sources: [KB.boldReds, KB.pairing],
    };
  }

  if (has(text, "thank", "thanks", "perfect", "great", "awesome")) {
    return {
      message: "You're welcome! Is there anything else I can help you with today?",
      intent: "chitchat",
      confidence: 0.9,
      tools: [],
      sources: [],
    };
  }

  // Unclear follow-up: lean on the conversation so far (multi-turn context).
  const previous = lastAssistantTopic(context);
  if (previous) {
    return {
      message: `Just to make sure I follow — is this still about ${previous}? Tell me a little more and I'll take it from there.`,
      intent: "refine.results",
      confidence: 0.55,
      tools: [],
      sources: [],
    };
  }

  return {
    message:
      "I can help with your orders, returns and refunds, delivery and pickup, your account, or finding the right bottle. What can I do for you?",
    intent: "education.wine_question",
    confidence: 0.4,
    tools: [],
    sources: [],
  };
}

function wait(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });
}

export async function mockChat(request: ChatRequest, context: ContextMessage[], signal?: AbortSignal): Promise<ChatResponse> {
  const started = performance.now();
  const text = request.message.toLowerCase();
  await wait(text.includes("simulate slow") ? 6000 : 700 + Math.random() * 900, signal);

  if (text.includes("simulate error")) {
    throw new Error("SipGuide couldn't reach the support service.");
  }

  const reply = replyFor(request, context);
  const pending: PendingActionOut | null = reply.pendingAction
    ? {
        ...reply.pendingAction,
        action_id: `act_${hex32()}`,
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      }
    : null;
  if (pending) issuedActions.set(pending.action_id, { tool: pending.tool, summary: pending.summary });

  return {
    session_id: request.session_id,
    run_id: `run_${hex32()}`,
    status: "completed",
    message: reply.message,
    intent: { name: reply.intent, confidence: reply.confidence },
    tools_used: reply.tools,
    kb_sources: reply.sources,
    pending_action: pending,
    requires_confirmation: pending !== null,
    executed_action: reply.executedAction ? { action_id: request.confirm_action_id ?? `act_${hex32()}`, ...reply.executedAction } : null,
    escalation: reply.escalation ?? null,
    llm_provider: "mock",
    duration_ms: Math.round(performance.now() - started),
  };
}
