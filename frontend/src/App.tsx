import { ChevronDown, Headset, Menu, SquarePen } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Composer, type ComposerHandle } from "./components/Composer";
import { EmptyState } from "./components/EmptyState";
import { Sidebar } from "./components/Sidebar";
import { TurnView } from "./components/TurnView";
import { announcementFor, conversationTickets, notePrefix, openActionTurn, supportStatus, type TicketInfo } from "./lib/status";
import { useChat } from "./state/useChat";

const TALK_TO_PERSON = "I'd like to talk to a person.";
/** Matches the pending line's switch to "taking longer" in TurnView. */
const SLOW_AFTER_MS = 5000;

/** Focus the prompt bar, except on touch devices where it would pop the keyboard over the answer. */
function focusIfFinePointer(target: ComposerHandle | null) {
  if (window.matchMedia("(pointer: fine)").matches) target?.focus();
}

export default function App() {
  const chat = useChat();
  const { active } = chat;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const composer = useRef<ComposerHandle>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const transcriptEnd = useRef<HTMLDivElement>(null);
  const announced = useRef<{ conversation?: string; turn?: string; status?: string }>({});
  /** Set when a starter is picked without a fine pointer: focus the new exchange once it renders. */
  const focusNewTurn = useRef(false);

  const busy = active?.turns.some((t) => t.status === "pending") ?? false;
  const lastTurn = active?.turns[active.turns.length - 1];
  const offerOpen = openActionTurn(active) !== null;
  const tickets = active ? conversationTickets(active) : [];
  /** The newest ticket: where "Add a note" goes. */
  const ticket = tickets.length ? tickets[tickets.length - 1].number : null;

  // Keep the newest exchange in view when a turn is added or answered.
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    transcriptEnd.current?.scrollIntoView({ block: "end", behavior: reduce ? "auto" : "smooth" });
  }, [active?.id, active?.turns.length, lastTurn?.status]);

  // One polite announcement per change to the newest turn. Switching conversations stays silent.
  useEffect(() => {
    const previous = announced.current;
    announced.current = { conversation: active?.id, turn: lastTurn?.id, status: lastTurn?.status };
    if (!lastTurn || previous.conversation !== active?.id) return;
    if (previous.turn === lastTurn.id && previous.status === lastTurn.status) return;
    setAnnouncement(announcementFor(lastTurn));
  }, [active?.id, lastTurn]);

  // Tell screen-reader users when an answer is slow, as the pending line does visually.
  useEffect(() => {
    if (lastTurn?.status !== "pending") return;
    const timer = setTimeout(() => setAnnouncement("Still checking. This is taking longer than usual."), SLOW_AFTER_MS);
    return () => clearTimeout(timer);
  }, [lastTurn?.id, lastTurn?.status]);

  // The starter button that had focus is gone once the conversation starts.
  useEffect(() => {
    if (!focusNewTurn.current || !active) return;
    focusNewTurn.current = false;
    document.querySelector<HTMLElement>(".turn:last-of-type")?.focus();
  }, [active]);

  useEffect(() => focusIfFinePointer(composer.current), []);

  /** Set when the drawer closes without a destination, so focus goes back to the menu button. */
  const returnFocus = useRef(false);
  const closeSidebar = useCallback(() => {
    returnFocus.current = true;
    setSidebarOpen(false);
  }, []);

  // Runs after <main> stops being inert; focusing earlier would silently fail.
  useEffect(() => {
    if (sidebarOpen || !returnFocus.current) return;
    returnFocus.current = false;
    const menu = menuButton.current;
    if (menu && getComputedStyle(menu).display !== "none") menu.focus();
  }, [sidebarOpen]);

  useEffect(() => {
    if (!sidebarOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeSidebar();
    // Widening past the drawer breakpoint turns the drawer back into a column.
    const wide = window.matchMedia("(min-width: 861px)");
    const onWide = () => wide.matches && setSidebarOpen(false);
    window.addEventListener("keydown", onKey);
    wide.addEventListener("change", onWide);
    return () => {
      window.removeEventListener("keydown", onKey);
      wide.removeEventListener("change", onWide);
    };
  }, [sidebarOpen, closeSidebar]);

  const startNew = useCallback(() => {
    chat.select(null);
    setSidebarOpen(false);
    composer.current?.focus();
  }, [chat]);

  const open = useCallback(
    (id: string) => {
      chat.select(id);
      setSidebarOpen(false);
      focusIfFinePointer(composer.current);
    },
    [chat],
  );

  // Never blocked: a pending answer is stopped first.
  const talkToPerson = useCallback(() => {
    chat.send(TALK_TO_PERSON, { interrupt: true });
  }, [chat]);

  const pickStarter = useCallback(
    (text: string) => {
      chat.send(text);
      if (window.matchMedia("(pointer: fine)").matches) composer.current?.focus();
      else focusNewTurn.current = true;
    },
    [chat],
  );

  return (
    <div className="app">
      <a className="skip-link" href="#composer-input">
        Skip to message box
      </a>

      <Sidebar
        conversations={chat.conversations}
        activeId={active?.id ?? null}
        open={sidebarOpen}
        onClose={closeSidebar}
        onNew={startNew}
        onSelect={open}
        onDelete={chat.remove}
        onClearAll={chat.clearAll}
      />
      <div className="scrim" data-open={sidebarOpen} onClick={closeSidebar} aria-hidden />

      {/* While the drawer is open on small screens, the page behind it is out of reach. */}
      <main className="chat" inert={sidebarOpen}>
        <header className="chat__head">
          <div className="chat__bar">
            <button
              type="button"
              className="icon-button chat__menu"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open history"
              aria-expanded={sidebarOpen}
              ref={menuButton}
            >
              <Menu size={20} strokeWidth={1.75} aria-hidden />
            </button>
            <h1 className="chat__title">{active ? active.title : "New conversation"}</h1>
            <button type="button" className="icon-button chat__new" onClick={startNew} aria-label="New conversation">
              <SquarePen size={18} strokeWidth={1.75} aria-hidden />
            </button>
          </div>
          {tickets.length > 0 && <TicketPanel tickets={tickets} />}
        </header>

        <div className="chat__scroll">
          {active ? (
            <section className="transcript" aria-label={`Conversation: ${active.title}`}>
              {active.turns.map((turn, i) => (
                <TurnView
                  key={turn.id}
                  turn={turn}
                  index={i}
                  conversationId={active.id}
                  isLatest={i === active.turns.length - 1}
                  busy={busy}
                  onRetry={() => chat.retry(active.id, turn.id)}
                  onDecide={(decision) => chat.decideAction(active.id, turn, decision)}
                  onTalkToPerson={talkToPerson}
                  onReopen={() => chat.requestReopen(active.id, turn)}
                  onAskAgain={() => chat.send(turn.human.content)}
                  ticket={ticket}
                />
              ))}
              <div ref={transcriptEnd} />
            </section>
          ) : (
            <EmptyState onPick={pickStarter} />
          )}
        </div>

        <div className="chat__composer">
          <Composer
            ref={composer}
            busy={busy}
            onSend={(text, noteFor) => chat.send(noteFor ? `${notePrefix(noteFor)} ${text}` : text)}
            onStop={() => active && chat.stop(active.id)}
            onTalkToPerson={talkToPerson}
            ticket={ticket}
            offerOpen={offerOpen}
          />
        </div>
      </main>

      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>
    </div>
  );
}

/** The one home for this conversation's tickets: what each is about, its status, and when to expect a reply. */
function TicketPanel({ tickets }: { tickets: TicketInfo[] }) {
  const team = supportStatus();
  // Small screens: one line until tapped, so the panel doesn't eat the conversation.
  const [open, setOpen] = useState(false);
  const newest = tickets[tickets.length - 1];
  return (
    <section className="tickets" aria-label="With our team" data-open={open}>
      <Headset size={16} strokeWidth={1.75} aria-hidden />
      <button type="button" className="tickets__toggle" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="tickets__toggle-text">
          {tickets.length > 1 ? `${tickets.length} tickets` : newest.number} · Waiting for our team
        </span>
        <ChevronDown size={16} strokeWidth={1.75} aria-hidden />
      </button>
      <ul>
        {tickets.map((t) => (
          <li key={t.number}>
            <p className="tickets__about">{t.about}</p>
            <p className="tickets__meta">
              <span>Waiting for our team</span>
              <span>
                Reply by email · <span data-online={team.online}>{team.label.replace("Team", "team")}</span>
              </span>
              <span className="tickets__number">{t.number}</span>
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
