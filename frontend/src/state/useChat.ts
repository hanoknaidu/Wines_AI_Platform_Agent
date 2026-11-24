import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";
import { agentClient } from "../api/agentClient";
import { config } from "../config";
import { buildAgentContext } from "../lib/context";
import { newConversationId, newMessageId, newTurnId } from "../lib/ids";
import { classifyReply, openActionTurn, REOPEN_PREFIX } from "../lib/status";
import { clearState, loadState, saveState } from "../lib/storage";
import { seedConversations } from "../mock/seedConversations";
import type { ActionDecision, ContextMessage, Conversation, Turn } from "../types";
import { chatReducer, type ChatState } from "./conversations";

function initialState(): ChatState {
  return loadState() ?? { conversations: seedConversations(), activeId: null };
}

export function useChat() {
  const [state, dispatch] = useReducer(chatReducer, undefined, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;
  /** In-flight requests by turn ID, so deleting a conversation can cancel them. */
  const inFlight = useRef(new Map<string, AbortController>());
  /** send() and decideAction() call each other; the ref breaks the cycle. */
  const decideRef = useRef<(conversationId: string, turn: Turn, decision: ActionDecision, typed?: string) => void>(() => {});

  useEffect(() => {
    saveState(state.conversations, state.activeId);
  }, [state]);

  useEffect(() => {
    const controllers = inFlight.current;
    return () => controllers.forEach((c) => c.abort());
  }, []);

  const run = useCallback(async (conversationId: string, turn: Turn, context: ContextMessage[]) => {
    const controller = new AbortController();
    inFlight.current.set(turn.id, controller);
    try {
      const response = await agentClient.chat(
        {
          customer_id: config.customerId,
          session_id: conversationId,
          message: turn.human.content,
          confirm_action_id: turn.confirmActionId ?? null,
          channel: config.channel,
        },
        context,
        controller.signal,
      );
      if (response.status === "failed") {
        dispatch({ type: "fail", conversationId, turnId: turn.id, error: response.message || "SipGuide couldn't finish that answer." });
        return;
      }
      const { message, session_id: _session, ...meta } = response;
      const now = new Date().toISOString();
      dispatch({
        type: "resolve",
        conversationId,
        turnId: turn.id,
        now,
        ai: { id: newMessageId(), role: "ai", content: message, createdAt: now, meta },
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      dispatch({
        type: "fail",
        conversationId,
        turnId: turn.id,
        error: error instanceof Error ? error.message : "Something went wrong.",
      });
    } finally {
      inFlight.current.delete(turn.id);
    }
  }, []);

  /** Stops any answer still pending in a conversation. */
  const stop = useCallback((conversationId: string) => {
    const conversation = stateRef.current.conversations.find((c) => c.id === conversationId);
    conversation?.turns
      .filter((t) => t.status === "pending")
      .forEach((t) => {
        inFlight.current.get(t.id)?.abort();
        dispatch({ type: "stop", conversationId, turnId: t.id });
      });
  }, []);

  /**
   * Sends a message into a conversation, creating it when `conversationId` is new.
   * While an offer is open, a typed unambiguous "yes" or "no" answers it (the
   * backend accepts the same); any other message moves on and closes it. A
   * casual yes ("ok, …") to an irreversible offer is held back: returns "held".
   * `interrupt` stops a pending answer first instead of refusing to send.
   */
  const send = useCallback(
    (
      text: string,
      options: { conversationId?: string | null; confirmActionId?: string; fromDecision?: boolean; interrupt?: boolean } = {},
    ): "sent" | "held" | "ignored" => {
      const content = text.trim().slice(0, config.maxMessageLength);
      if (!content) return "ignored";
      const current = stateRef.current;
      const conversationId = options.conversationId ?? current.activeId ?? newConversationId();
      const conversation = current.conversations.find((c) => c.id === conversationId);
      if (conversation?.turns.some((t) => t.status === "pending")) {
        if (!options.interrupt) return "ignored";
        stop(conversationId);
      }

      if (!options.fromDecision && !options.confirmActionId && conversation) {
        const offer = openActionTurn(conversation);
        if (offer) {
          const reply = classifyReply(content);
          if (reply === "hold") return "held";
          if (reply !== "other") {
            decideRef.current(conversationId, offer, reply === "confirm" ? "confirmed" : "declined", content);
            return "sent";
          }
        }
      }

      const now = new Date().toISOString();
      const turn: Turn = {
        id: newTurnId(),
        human: { id: newMessageId(), role: "human", content, createdAt: now },
        ai: null,
        status: "pending",
        confirmActionId: options.confirmActionId ?? null,
      };
      const context = conversation ? buildAgentContext(conversation, config.contextTurnLimit) : [];
      dispatch({ type: "send", conversationId, turn, now });
      void run(conversationId, turn, context);
      return "sent";
    },
    [run, stop],
  );

  const retry = useCallback(
    (conversationId: string, turnId: string) => {
      const conversation = stateRef.current.conversations.find((c) => c.id === conversationId);
      const index = conversation?.turns.findIndex((t) => t.id === turnId) ?? -1;
      if (!conversation || index < 0) return;
      const earlier: Conversation = { ...conversation, turns: conversation.turns.slice(0, index) };
      dispatch({ type: "retry", conversationId, turnId });
      void run(conversationId, conversation.turns[index], buildAgentContext(earlier, config.contextTurnLimit));
    },
    [run],
  );

  /** Answers a proposed action, with the button's words or the customer's own typed reply. */
  const decideAction = useCallback(
    (conversationId: string, turn: Turn, decision: ActionDecision, typed?: string) => {
      const action = turn.ai?.meta?.pending_action;
      if (!action || turn.actionDecision) return;
      dispatch({ type: "decideAction", conversationId, turnId: turn.id, decision });
      if (decision === "confirmed") {
        const text = typed ?? `Yes, go ahead: ${action.summary.charAt(0).toLowerCase()}${action.summary.slice(1)}.`;
        send(text, { conversationId, confirmActionId: action.action_id, fromDecision: true });
      } else {
        send(typed ?? "Not now, thanks.", { conversationId, fromDecision: true });
      }
    },
    [send],
  );
  decideRef.current = decideAction;

  /**
   * A closed or expired offer can't simply be reopened: the request goes to the
   * team as a ticket, and nothing happens until they approve it.
   */
  const requestReopen = useCallback(
    (conversationId: string, turn: Turn) => {
      const action = turn.ai?.meta?.pending_action;
      if (!action || turn.reopenRequested) return;
      dispatch({ type: "requestReopen", conversationId, turnId: turn.id });
      send(`${REOPEN_PREFIX} ${action.summary}.`, { conversationId, fromDecision: true, interrupt: true });
    },
    [send],
  );

  const select = useCallback((conversationId: string | null) => dispatch({ type: "select", conversationId }), []);

  const remove = useCallback((conversationId: string) => {
    const conversation = stateRef.current.conversations.find((c) => c.id === conversationId);
    conversation?.turns.forEach((t) => inFlight.current.get(t.id)?.abort());
    dispatch({ type: "delete", conversationId });
  }, []);

  const clearAll = useCallback(() => {
    inFlight.current.forEach((c) => c.abort());
    clearState();
    dispatch({ type: "clearAll" });
  }, []);

  const active = useMemo(
    () => state.conversations.find((c) => c.id === state.activeId) ?? null,
    [state.conversations, state.activeId],
  );

  return { conversations: state.conversations, active, send, stop, retry, decideAction, requestReopen, select, remove, clearAll };
}
