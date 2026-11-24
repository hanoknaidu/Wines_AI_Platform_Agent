const MAX_TITLE_LENGTH = 48;
const GREETING = /^(hi|hello|hey|good (morning|afternoon|evening))[\s,!.]+/i;

/**
 * Builds a conversation title from the customer's first question:
 * collapse whitespace, drop a leading greeting and trailing punctuation,
 * cut at a word boundary, and capitalize the first letter.
 */
export function titleFromMessage(message: string): string {
  let text = message.replace(/\s+/g, " ").trim();
  const withoutGreeting = text.replace(GREETING, "").trim();
  if (withoutGreeting.length > 0) text = withoutGreeting;
  text = text.replace(/[\s?!.,;:]+$/, "");
  if (text.length === 0) return "New conversation";

  if (text.length > MAX_TITLE_LENGTH) {
    const cut = text.slice(0, MAX_TITLE_LENGTH + 1);
    const lastSpace = cut.lastIndexOf(" ");
    text = (lastSpace > MAX_TITLE_LENGTH / 2 ? cut.slice(0, lastSpace) : cut.slice(0, MAX_TITLE_LENGTH)).replace(/[\s,;:]+$/, "") + "…";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}
