"""Response filtering and PII redaction helpers.

* mask_email / mask_phone: how contact data is shown in API responses.
* redact_text: scrubs free text (chat messages, logs, traces) of card numbers,
  SSNs, emails and phone numbers. The agent must never collect or echo those
  (KB A-74), and traces must not become a PII store."""
from __future__ import annotations

import re

_EMAIL = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE = re.compile(r"(?<![\w-])(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b")


def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    return f"***-***-{digits[-4:]}" if len(digits) >= 4 else "***"


def mask_street(line1: str | None) -> str | None:
    """'25 Willowmere Street' -> '** W*** Street' (agent-facing views)."""
    if not line1:
        return line1
    parts = line1.split()
    out = []
    for i, part in enumerate(parts):
        if any(ch.isdigit() for ch in part):
            out.append("**")
        elif i == len(parts) - 1:
            out.append(part)  # keep the street type ("Street", "Avenue")
        else:
            out.append(part[0] + "***")
    return " ".join(out)


def _luhn_ok(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)][::-1]
    if not 13 <= len(digits) <= 19:
        return False
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


def contains_card_number(text: str) -> bool:
    return any(_luhn_ok(m.group(0)) for m in _CARD.finditer(text or ""))


def redact_payment_data(text: str | None) -> str | None:
    """Card numbers and SSNs only (used on agent output, where store phone
    numbers and emails are legitimate content)."""
    if not text:
        return text
    text = _CARD.sub(lambda m: "[REDACTED_CARD]" if _luhn_ok(m.group(0)) else m.group(0), text)
    return _SSN.sub("[REDACTED_SSN]", text)


def redact_text(text: str | None) -> str | None:
    if not text:
        return text
    text = _CARD.sub(lambda m: "[REDACTED_CARD]" if _luhn_ok(m.group(0)) else m.group(0), text)
    text = _SSN.sub("[REDACTED_SSN]", text)
    text = _EMAIL.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", text)
    text = _PHONE.sub(lambda m: mask_phone(m.group(0)) or "", text)
    return text


SENSITIVE_KEYS = {"password", "token", "authorization", "jwt", "secret", "card_number", "cvv", "ssn", "api_key"}


def redact_mapping(value, _depth: int = 0):
    """Recursively redact a JSON-like structure for trace storage."""
    if _depth > 6:
        return "…"
    if isinstance(value, dict):
        return {
            str(k): ("[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else redact_mapping(v, _depth + 1))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_mapping(v, _depth + 1) for v in value[:50]]
    if isinstance(value, str):
        return redact_text(value[:2000])
    return value
