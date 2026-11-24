/** App-wide settings. Change the brand here; nothing else hard-codes it. */
export const config = {
  appName: "SipGuide AI",
  /** Fictional seed customer (C-100005, Aisha) until sign-in lands in Phase 2. */
  customerId: "C-100005",
  customerFirstName: "Aisha",
  channel: "web_chat" as const,
  /** Mirrors ChatRequest.message max_length in app/schemas/agent.py. */
  maxMessageLength: 4000,
  /**
   * Human support hours, from the KB business profile (9:00 am – 9:00 pm ET, 7 days).
   * Phase 2: read them (and holiday exceptions) from get_store_info instead.
   */
  supportHours: { open: 9, close: 21, timeZone: "America/New_York" },
  /** Number of earlier turns sent to the agent as context. */
  contextTurnLimit: 10,
  /** Shows conversation / turn / message IDs under each turn. On in dev builds only. */
  showDebugDetails: import.meta.env.DEV,
  storageKey: "sipguide.conversations.v1",
};
