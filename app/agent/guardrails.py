"""Input and output guardrails around the LLM.

Input: redact payment/ID data before it is stored or sent to the model (A-74),
flag compliance signals (handled before any tool call) and prompt-injection
attempts (logged; tools are customer-scoped regardless).
Output: mask PII the model may echo, strip any internal tags."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.masking import contains_card_number, redact_payment_data, redact_text

INJECTION_RE = re.compile(
    r"\b(ignore (all |any |the )?(previous|prior|above) (instructions|rules)|system prompt|developer mode|"
    r"you are now|act as (an? )?(admin|staff|developer)|reveal (your|the) (prompt|instructions)|"
    r"other customers?'? (orders|data))\b", re.I)
OUT_OF_STATE_RE = re.compile(
    r"\b(ship|deliver|send)\w*\b.{0,40}\b(california|florida|texas|connecticut|pennsylvania|massachusetts|"
    r"illinois|ohio|georgia|virginia|washington|colorado|out of state|another state|canada)\b", re.I)
_TAGS = re.compile(r"</?(thinking|system|tool_use|tool_result|context)[^>]*>", re.I)


@dataclass
class InputCheck:
    text: str  # redacted text safe to store and send to the model
    flags: list[str] = field(default_factory=list)


def check_input(message: str) -> InputCheck:
    flags = []
    if contains_card_number(message):
        flags.append("payment_data_shared")
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", message):
        flags.append("ssn_shared")
    if INJECTION_RE.search(message):
        flags.append("prompt_injection_suspected")
    if OUT_OF_STATE_RE.search(message):
        flags.append("out_of_state_request")
    return InputCheck(redact_text(message.strip()) or "", flags)


def sanitize_output(text: str) -> str:
    return redact_payment_data(_TAGS.sub("", text or "").strip()) or ""
