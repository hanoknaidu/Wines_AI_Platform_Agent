/**
 * Domain model for the chat UI.
 *
 * Conversation ─┬─ id (Conversation ID, also sent to the backend as `session_id`)
 *               ├─ title (generated from the first human message)
 *               └─ turns[] (ordered)
 *                    ├─ human: Message (own Message ID)
 *                    └─ ai:    Message | null (own Message ID; null while the agent is working)
 */

// ---------------------------------------------------------------------------
// Backend contract: mirrors app/schemas/agent.py (snake_case JSON on the wire)
// ---------------------------------------------------------------------------

export interface IntentOut {
  name: string;
  confidence: number;
}

export interface KbSource {
  id: string;
  title: string;
  section: string;
}

export interface PendingActionOut {
  action_id: string;
  tool: string;
  summary: string;
  expires_at: string;
}

/** What a confirmed action did (app/agent/service.py _executed_out). */
export interface ExecutedActionOut {
  action_id: string;
  tool: string;
  ok: boolean;
  /** order_id, rma_number, refund_id, amount (decimal string), ticket_number, status */
  references: Record<string, string | number | null>;
}

export interface EscalationOut {
  ticket_number: string | null;
  priority: string | null;
  reason_code: string | null;
}

/** POST /api/v1/agent/chat request body. */
export interface ChatRequest {
  customer_id: string;
  session_id: string;
  message: string;
  confirm_action_id: string | null;
  channel: "web_chat" | "mobile_app" | "sms";
}

/** POST /api/v1/agent/chat response body. */
export interface ChatResponse {
  session_id: string;
  run_id: string;
  status: "completed" | "failed";
  message: string;
  intent: IntentOut | null;
  tools_used: string[];
  kb_sources: KbSource[];
  pending_action: PendingActionOut | null;
  requires_confirmation: boolean;
  executed_action: ExecutedActionOut | null;
  escalation: EscalationOut | null;
  llm_provider: string;
  duration_ms: number;
}

/** One prior message, in order, handed to the agent as conversation context. */
export interface ContextMessage {
  message_id: string;
  role: "user" | "assistant";
  content: string;
}

// ---------------------------------------------------------------------------
// Frontend state
// ---------------------------------------------------------------------------

/** Agent metadata kept on an AI message (everything in ChatResponse except the text). */
export type AgentMeta = Omit<ChatResponse, "message" | "session_id">;

export interface Message {
  id: string;
  role: "human" | "ai";
  content: string;
  createdAt: string;
  /** Only on AI messages. */
  meta?: AgentMeta;
}

export type TurnStatus = "pending" | "complete" | "error";

/** What the customer did with an action the agent proposed in this turn. */
export type ActionDecision = "confirmed" | "declined";

export interface Turn {
  id: string;
  human: Message;
  ai: Message | null;
  status: TurnStatus;
  error?: string;
  /** The customer stopped this answer before it arrived. */
  stopped?: boolean;
  /** Set when this turn's human message confirms an action proposed in an earlier turn. */
  confirmActionId?: string | null;
  /** The customer asked the team to review reopening this turn's closed or expired offer. */
  reopenRequested?: boolean;
  /** Set on a turn whose AI message proposed an action, once the customer answers it. */
  actionDecision?: ActionDecision;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turns: Turn[];
}
