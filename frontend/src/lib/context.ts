import type { ContextMessage, Conversation } from "../types";

/**
 * Earlier turns of a conversation, oldest first, as the agent will receive them.
 * Only completed turns count; a failed or pending turn has no answer to pass on.
 * `limit` keeps the most recent N turns so the payload stays bounded.
 */
export function buildAgentContext(conversation: Conversation, limit: number): ContextMessage[] {
  const complete = conversation.turns.filter((t) => t.status === "complete" && t.ai);
  return complete.slice(-limit).flatMap((turn) => [
    { message_id: turn.human.id, role: "user" as const, content: turn.human.content },
    { message_id: turn.ai!.id, role: "assistant" as const, content: turn.ai!.content },
  ]);
}
