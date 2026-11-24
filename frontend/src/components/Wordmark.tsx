import { config } from "../config";

/** The SipGuide mark: a glass outline drawn as one stroke, beside the serif name. */
export function Wordmark() {
  const [name, suffix] = config.appName.split(/\s(?=AI$)/);
  return (
    <span className="wordmark">
      <svg className="wordmark__glass" viewBox="0 0 24 24" aria-hidden>
        <path d="M7 3h10l-.5 6.2a4.5 4.5 0 0 1-9 0L7 3Z" />
        <path d="M7.3 7h9.4" />
        <path d="M12 13.7V20m-3.5 1h7" />
      </svg>
      <span className="wordmark__name">{name}</span>
      {suffix && <span className="wordmark__suffix">{suffix}</span>}
    </span>
  );
}
