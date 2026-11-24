/**
 * Unique IDs. Every ID is a prefix plus 32 hex characters, so a Conversation ID
 * also passes the backend's `session_id` pattern ^[A-Za-z0-9_-]{4,100}$.
 */
export function hex32(): string {
  // randomUUID needs a secure context (https or localhost); getRandomValues does not.
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export const newConversationId = () => `conv_${hex32()}`;
export const newTurnId = () => `turn_${hex32()}`;
export const newMessageId = () => `msg_${hex32()}`;
