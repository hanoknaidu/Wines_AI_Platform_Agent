import { Check, CircleAlert, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { config } from "../config";
import { formatTime } from "../lib/dates";
import { actionLabels, actionName, actionState, outcomeOf, VERDICT_LABELS, verdictOf } from "../lib/status";
import type { ActionDecision, Turn } from "../types";
import { RichText } from "./RichText";

interface TurnViewProps {
  turn: Turn;
  conversationId: string;
  index: number;
  /** Only the latest turn's pending action can still be answered. */
  isLatest: boolean;
  busy: boolean;
  onRetry: () => void;
  onDecide: (decision: ActionDecision) => void;
  onTalkToPerson: () => void;
  onReopen: () => void;
  onAskAgain: () => void;
  /** Open ticket in this conversation: a person already has it, so don't offer a new hand-off. */
  ticket: string | null;
}

const TOPIC_LABELS: Record<string, string> = {
  order: "Orders",
  return: "Returns",
  refund: "Refunds",
  claim: "Claims",
  delivery: "Delivery",
  shipping: "Shipping",
  pickup: "Pickup",
  recommend: "Recommendations",
  human: "Human support",
  compliance: "Store policy",
  account: "Account",
};

/** After this long, the pending line admits the wait. */
const SLOW_AFTER_MS = 5000;

function topicOf(intent: string | undefined): string | null {
  if (!intent) return null;
  return TOPIC_LABELS[intent.split(".")[0]] ?? null;
}

/** Re-renders once when `at` (an ISO time) passes, so an offer can expire on screen. */
function useRerenderAt(at: string | null) {
  const [, tick] = useState(0);
  useEffect(() => {
    if (!at) return;
    const delay = Date.parse(at) - Date.now();
    if (delay <= 0) return;
    const timer = setTimeout(() => tick((n) => n + 1), Math.min(delay + 50, 2 ** 31 - 1));
    return () => clearTimeout(timer);
  }, [at]);
}

function useSlow(pending: boolean) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!pending) return;
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => clearTimeout(timer);
  }, [pending]);
  return slow;
}

export function TurnView({
  turn,
  conversationId,
  index,
  isLatest,
  busy,
  onRetry,
  onDecide,
  onTalkToPerson,
  onReopen,
  onAskAgain,
  ticket,
}: TurnViewProps) {
  const meta = turn.ai?.meta;
  const action = meta?.pending_action ?? null;
  const topic = topicOf(meta?.intent?.name);
  const article = useRef<HTMLElement>(null);
  const actionBox = useRef<HTMLDivElement>(null);
  const slow = useSlow(turn.status === "pending");

  const state = actionState(turn, isLatest);
  useRerenderAt(state === "open" ? (action?.expires_at ?? null) : null);
  const verdict = verdictOf(turn, isLatest);
  const outcome = turn.status === "complete" ? outcomeOf(turn) : null;
  const labels = action ? actionLabels(action.tool) : null;

  // Buttons unmount once answered; keep keyboard and screen-reader focus on
  // something that stays, instead of dropping it to <body>.
  function decide(decision: ActionDecision) {
    actionBox.current?.focus();
    onDecide(decision);
  }

  function retry() {
    article.current?.focus();
    onRetry();
  }

  return (
    <article className="turn" aria-label={`Exchange ${index + 1}`} ref={article} tabIndex={-1}>
      <div className="message message--human">
        <p className="sr-only">You said:</p>
        <div className="message__bubble">{turn.human.content}</div>
      </div>

      <div className="message message--ai">
        <p className="sr-only">SipGuide replied:</p>

        {turn.status === "pending" && (
          <div className="thinking">
            <span className="thinking__dots" aria-hidden>
              <span />
              <span />
              <span />
            </span>
            <span className="thinking__label">
              {slow ? "Still checking. This is taking longer than usual…" : "Checking your account and our guides…"}
            </span>
          </div>
        )}

        {turn.status === "error" && (
          <div className="turn-error" data-stopped={turn.stopped ?? false}>
            <p className="turn-error__text">
              <strong>{turn.stopped ? "You stopped this answer." : "That answer didn't come through."}</strong>{" "}
              {!turn.stopped && turn.error}{" "}
              {turn.confirmActionId
                ? "We can't tell yet whether your request went through. Trying again is safe: it won't be done twice."
                : "Nothing on your account has changed."}
            </p>
            <div className="turn-error__actions">
              {isLatest ? (
                <button type="button" className="button button--quiet" onClick={retry} disabled={busy}>
                  <RotateCcw size={15} strokeWidth={1.75} aria-hidden />
                  Try again
                </button>
              ) : (
                // Retrying in place would answer out of order: ask it again at the end instead.
                <button type="button" className="button button--quiet" onClick={onAskAgain} disabled={busy}>
                  <RotateCcw size={15} strokeWidth={1.75} aria-hidden />
                  Ask again
                </button>
              )}
              {!ticket && (
                <button type="button" className="text-button" onClick={onTalkToPerson}>
                  Talk to a person
                </button>
              )}
            </div>
          </div>
        )}

        {turn.status === "complete" && turn.ai && (
          <>
            <div className="answer">
              <RichText text={turn.ai.content} />
            </div>

            {outcome && (
              <div
                className="outcome"
                data-kind={outcome.ok ? "done" : "failed"}
                role="group"
                aria-label={outcome.title}
              >
                <p className="outcome__title">
                  {outcome.ok ? (
                    <Check size={16} strokeWidth={2} aria-hidden />
                  ) : (
                    <CircleAlert size={16} strokeWidth={1.75} aria-hidden />
                  )}
                  {outcome.title}
                </p>
                {outcome.rows.length > 0 && (
                  <dl className="outcome__rows">
                    {outcome.rows.map((r) => (
                      <div key={r.label}>
                        <dt>{r.label}</dt>
                        <dd>{r.value}</dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
            )}

            {action && labels && state && (
              <div
                className="action"
                data-state={state}
                ref={actionBox}
                tabIndex={-1}
                role="group"
                aria-label={actionName(action.tool, state)}
              >
                <p className="action__summary">{action.summary}</p>
                {state === "open" && (
                  <>
                    <p className="action__note">
                      Nothing happens until you choose. This offer is open until {formatTime(action.expires_at)}.
                    </p>
                    <div className="action__buttons">
                      <button type="button" className="button button--primary" onClick={() => decide("confirmed")} disabled={busy}>
                        {labels.confirm}
                      </button>
                      <button type="button" className="button button--quiet" onClick={() => decide("declined")} disabled={busy}>
                        {labels.decline}
                      </button>
                    </div>
                  </>
                )}
                {state === "confirmed" && (
                  <p className="action__status">
                    <Check size={15} strokeWidth={2} aria-hidden /> You said yes
                  </p>
                )}
                {state === "declined" && <p className="action__status">You said no. Nothing was changed.</p>}
                {state === "closed" && <p className="action__status">Closed when the conversation moved on. Nothing was changed.</p>}
                {state === "expired" && (
                  <p className="action__status">This offer expired at {formatTime(action.expires_at)}. Nothing was changed.</p>
                )}
                {(state === "closed" || state === "expired") &&
                  (turn.reopenRequested ? (
                    <p className="action__status action__status--review">
                      Sent to our team for review. Nothing changes until they approve it.
                    </p>
                  ) : (
                    <div className="action__buttons">
                      <button type="button" className="button button--quiet" onClick={onReopen} disabled={busy}>
                        Ask our team to reopen
                      </button>
                    </div>
                  ))}
              </div>
            )}

            <p className="byline">
              {verdict && (
                <span className="byline__verdict" data-verdict={verdict}>
                  {VERDICT_LABELS[verdict]}
                </span>
              )}
              {topic && verdict !== "with_team" && <span>{topic}</span>}
              <time dateTime={turn.ai.createdAt}>{formatTime(turn.ai.createdAt)}</time>
              {meta && meta.kb_sources.length > 0 && (
                <span className="byline__sources">
                  From our guides: {meta.kb_sources.map((s) => s.title).join("; ")}
                </span>
              )}
            </p>
          </>
        )}

        {config.showDebugDetails && (
          <details className="debug">
            <summary>Developer IDs</summary>
            <dl>
              <dt>Conversation</dt>
              <dd>{conversationId}</dd>
              <dt>Turn {index + 1}</dt>
              <dd>{turn.id}</dd>
              <dt>Human message</dt>
              <dd>{turn.human.id}</dd>
              <dt>AI message</dt>
              <dd>{turn.ai?.id ?? "—"}</dd>
              {meta && (
                <>
                  <dt>Run</dt>
                  <dd>{meta.run_id}</dd>
                  <dt>Intent</dt>
                  <dd>
                    {meta.intent?.name ?? "—"} ({meta.intent?.confidence.toFixed(2) ?? "—"})
                  </dd>
                  <dt>Tools</dt>
                  <dd>{meta.tools_used.join(", ") || "—"}</dd>
                  {meta.kb_sources.length > 0 && (
                    <>
                      <dt>Sources</dt>
                      <dd>{meta.kb_sources.map((s) => `${s.id} (${s.section})`).join(", ")}</dd>
                    </>
                  )}
                </>
              )}
              {turn.confirmActionId && (
                <>
                  <dt>Confirms</dt>
                  <dd>{turn.confirmActionId}</dd>
                </>
              )}
            </dl>
          </details>
        )}
      </div>
    </article>
  );
}
