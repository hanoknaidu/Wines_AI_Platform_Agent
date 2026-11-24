import { Headset, SquarePen, Trash2, X } from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { config } from "../config";
import { groupByRecency } from "../lib/dates";
import { conversationStatus } from "../lib/status";
import type { Conversation } from "../types";
import { Wordmark } from "./Wordmark";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  open: boolean;
  onClose: () => void;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClearAll: () => void;
}

export function Sidebar({ conversations, activeId, open, onClose, onNew, onSelect, onDelete, onClearAll }: SidebarProps) {
  const groups = useMemo(() => groupByRecency(conversations), [conversations]);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [confirmingClear, setConfirmingClear] = useState(false);
  const root = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  /** Where focus goes after the control that had it unmounts (data-focus-key). */
  const pendingFocus = useRef<string | null>(null);

  useLayoutEffect(() => {
    const key = pendingFocus.current;
    if (!key) return;
    pendingFocus.current = null;
    root.current?.querySelector<HTMLElement>(`[data-focus-key="${key}"]`)?.focus();
  });

  // Opening the drawer moves focus into it. Wait a frame: the drawer only becomes
  // visible (and focusable) once its visibility transition has started.
  useEffect(() => {
    if (!open) return;
    const frame = requestAnimationFrame(() => closeButton.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [open]);

  function confirmDelete(id: string) {
    const order = groups.flatMap((g) => g.items);
    const i = order.findIndex((c) => c.id === id);
    const next = order[i + 1] ?? order[i - 1];
    pendingFocus.current = next ? `open:${next.id}` : "new";
    setConfirmingId(null);
    onDelete(id);
  }

  return (
    <aside className="sidebar" data-open={open} aria-label="Conversation history" ref={root}>
      <div className="sidebar__head">
        <Wordmark />
        <button type="button" className="icon-button sidebar__close" onClick={onClose} aria-label="Close history" ref={closeButton}>
          <X size={18} strokeWidth={1.75} aria-hidden />
        </button>
      </div>

      <button type="button" className="button button--primary sidebar__new" onClick={onNew} data-focus-key="new">
        <SquarePen size={16} strokeWidth={1.75} aria-hidden />
        New conversation
      </button>

      <nav className="history" aria-label="Past conversations">
        {groups.length === 0 && (
          <p className="history__empty">Your conversations will appear here, so you can pick one up again later.</p>
        )}
        {groups.map((group) => {
          const labelId = `history-${group.label.replace(/\W+/g, "-").toLowerCase()}`;
          return (
            <section key={group.label} className="history__group">
              <p className="history__label" id={labelId}>
                {group.label}
              </p>
              <ul aria-labelledby={labelId}>
                {group.items.map((c) => {
                  const confirming = confirmingId === c.id;
                  const status = conversationStatus(c);
                  return (
                    <li key={c.id} className="history__item" data-active={c.id === activeId} data-confirming={confirming}>
                      {confirming ? (
                        <div className="history__confirm" role="group" aria-label={`Delete “${c.title}”?`}>
                          <span>Delete this conversation?</span>
                          <button type="button" className="text-button text-button--danger" onClick={() => confirmDelete(c.id)}>
                            Delete
                          </button>
                          <button
                            type="button"
                            className="text-button"
                            onClick={() => {
                              pendingFocus.current = `delete:${c.id}`;
                              setConfirmingId(null);
                            }}
                            autoFocus
                          >
                            Keep
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="history__link"
                            onClick={() => onSelect(c.id)}
                            aria-current={c.id === activeId ? "page" : undefined}
                            data-focus-key={`open:${c.id}`}
                          >
                            <span className="history__title">{c.title}</span>
                            {status.needsYou && (
                              <span className="history__flag history__flag--needs">
                                <span className="sr-only">, waiting for your answer</span>
                              </span>
                            )}
                            {status.ticket && (
                              <span className="history__flag history__flag--ticket">
                                <Headset size={14} strokeWidth={1.75} aria-hidden />
                                <span className="sr-only">, with our team (ticket {status.ticket})</span>
                              </span>
                            )}
                          </button>
                          <button
                            type="button"
                            className="icon-button history__delete"
                            onClick={() => setConfirmingId(c.id)}
                            aria-label={`Delete “${c.title}”`}
                            data-focus-key={`delete:${c.id}`}
                          >
                            <Trash2 size={15} strokeWidth={1.75} aria-hidden />
                          </button>
                        </>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          );
        })}
      </nav>

      <footer className="sidebar__foot">
        <div className="account">
          <span className="account__avatar" aria-hidden>
            {config.customerFirstName.charAt(0)}
          </span>
          <span className="account__name">
            {config.customerFirstName}
            <span className="account__meta">Demo account · {config.customerId}</span>
          </span>
        </div>
        {conversations.length > 0 &&
          (confirmingClear ? (
            <div className="sidebar__clear" role="group" aria-label="Clear all history?">
              <span>Clear all history?</span>
              <button
                type="button"
                className="text-button text-button--danger"
                onClick={() => {
                  pendingFocus.current = "new";
                  setConfirmingClear(false);
                  onClearAll();
                }}
              >
                Clear
              </button>
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  pendingFocus.current = "clear";
                  setConfirmingClear(false);
                }}
                autoFocus
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="text-button sidebar__clear-trigger"
              onClick={() => setConfirmingClear(true)}
              data-focus-key="clear"
            >
              Clear history
            </button>
          ))}
      </footer>
    </aside>
  );
}
