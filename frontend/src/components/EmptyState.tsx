import { config } from "../config";

/** Problems first: most people open support chat because something went wrong. */
const STARTERS = [
  { label: "Where is my latest order?", hint: "Status, pickup and delivery" },
  { label: "Something arrived broken or wrong", hint: "Damaged, corked or missing bottles" },
  { label: "I'd like to return a bottle", hint: "Returns and refunds" },
  { label: "Do you deliver to my area?", hint: "New Jersey and New York" },
];

export function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="empty">
      <h2 className="empty__title">How can I help, {config.customerFirstName}?</h2>
      <p className="empty__lede">
        I'm SipGuide, the store's AI assistant. I can check on an order, sort out a return or a damaged delivery, and
        answer questions about wine. You can ask for a person at any time.
      </p>
      <ul className="starters" aria-label="Common questions">
        {STARTERS.map((s) => (
          <li key={s.label}>
            <button type="button" className="starter" onClick={() => onPick(s.label)}>
              <span className="starter__label">{s.label}</span>
              <span className="starter__hint">{s.hint}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
