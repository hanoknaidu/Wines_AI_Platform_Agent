import { ArrowUp, Square, X } from "lucide-react";
import { forwardRef, useImperativeHandle, useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { config } from "../config";

interface ComposerProps {
  busy: boolean;
  /** "held": the message was not sent (a casual yes to something irreversible); keep the text. */
  /** `noteFor`: the message is a note for this open ticket. */
  onSend: (text: string, noteFor?: string) => "sent" | "held" | "ignored";
  onStop: () => void;
  onTalkToPerson: () => void;
  /** Newest open ticket: "Talk to a person" becomes "Add a note to TKT-…". */
  ticket: string | null;
  /** An offer above is waiting for a yes or no. */
  offerOpen: boolean;
}

export interface ComposerHandle {
  focus: () => void;
}

const COUNTER_THRESHOLD = config.maxMessageLength - 400;

export const Composer = forwardRef<ComposerHandle, ComposerProps>(function Composer({ busy, onSend, onStop, onTalkToPerson, ticket, offerOpen }, ref) {
  const [text, setText] = useState("");
  const [held, setHeld] = useState(false);
  const [noteFor, setNoteFor] = useState<string | null>(null);
  if (noteFor && noteFor !== ticket) setNoteFor(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  useImperativeHandle(ref, () => ({ focus: () => textarea.current?.focus() }), []);

  // Grow with the content, up to the CSS max-height.
  useLayoutEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  const canSend = text.trim().length > 0 && !busy;

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSend) return;
    const result = onSend(text, noteFor ?? undefined);
    setHeld(result === "held");
    if (result !== "held") {
      setText("");
      setNoteFor(null);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      {noteFor && (
        <p className="composer__mode">
          <span>
            Adding a note to ticket <strong>{noteFor}</strong>
          </span>
          <button
            type="button"
            className="icon-button composer__mode-close"
            onClick={() => {
              setNoteFor(null);
              textarea.current?.focus();
            }}
            aria-label="Cancel note"
          >
            <X size={14} strokeWidth={2} aria-hidden />
          </button>
        </p>
      )}
      <div className="composer__field">
        <label htmlFor="composer-input" className="sr-only">
          Message SipGuide AI
        </label>
        <textarea
          id="composer-input"
          ref={textarea}
          rows={1}
          value={text}
          maxLength={config.maxMessageLength}
          placeholder={noteFor ? "Write your note for our team…" : "Ask about orders, returns or wine…"}
          onChange={(e) => {
            setText(e.target.value);
            setHeld(false);
          }}
          onKeyDown={onKeyDown}
          autoComplete="off"
          enterKeyHint="send"
        />
        {busy ? (
          <button type="button" className="composer__send composer__send--stop" onClick={onStop} aria-label="Stop answer">
            <Square size={12} strokeWidth={0} fill="currentColor" aria-hidden />
          </button>
        ) : (
          <button type="submit" className="composer__send" disabled={!canSend} aria-label="Send message">
            <ArrowUp size={18} strokeWidth={2} aria-hidden />
          </button>
        )}
      </div>
      <p className="composer__note">
        {held ? (
          <span className="composer__held" role="alert">
            To go ahead, please use the button above or type yes.
          </span>
        ) : text.length >= COUNTER_THRESHOLD ? (
          <span className="composer__count">{config.maxMessageLength - text.length} characters left</span>
        ) : busy ? (
          <span>SipGuide is answering…</span>
        ) : offerOpen ? (
          <span>Reply yes or no to the offer, or ask something else.</span>
        ) : (
          <span>SipGuide is an AI assistant and can make mistakes.</span>
        )}
        {ticket ? (
          <button
            type="button"
            className="composer__person"
            onClick={() => {
              setNoteFor(ticket);
              textarea.current?.focus();
            }}
            aria-pressed={noteFor === ticket}
          >
            Add a note to {ticket}
          </button>
        ) : (
          <button type="button" className="composer__person" onClick={onTalkToPerson}>
            Talk to a person
          </button>
        )}
      </p>
    </form>
  );
});
