import { mockChat } from "../mock/mockAgent";
import type { ChatRequest, ChatResponse, ContextMessage } from "../types";

/**
 * The one seam between the UI and the agent.
 *
 * Phase 1: `mockAgentClient` answers locally.
 * Phase 2: add an HTTP client that POSTs `request` to /api/v1/agent/chat with
 * the customer's JWT. `context` is the ordered list of earlier turns. Today's
 * ChatRequest schema forbids extra fields, so the backend must either accept a
 * `context` field or rebuild it from the stored session messages.
 */
export interface AgentClient {
  chat(request: ChatRequest, context: ContextMessage[], signal?: AbortSignal): Promise<ChatResponse>;
}

export const mockAgentClient: AgentClient = { chat: mockChat };

export const agentClient: AgentClient = mockAgentClient;
