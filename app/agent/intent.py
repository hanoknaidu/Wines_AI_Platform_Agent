"""Fast, deterministic intent + entity extraction (KB intent taxonomy names).

Runs on every turn before the LLM. With Claude, the result is a routing hint
and trace metadata (the LLM still chooses tools); in rule-based mode it drives
the planner. Confidence follows KB-SYS-005 bands (>=0.75 route, 0.5-0.75
confirm, <0.5 clarify)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ORDER_RE = re.compile(r"\bWA-?\s?(\d{6})\b", re.I)
RMA_RE = re.compile(r"\bRMA-?(\d{6})\b", re.I)
TICKET_RE = re.compile(r"\bTKT-?(\d{6})\b", re.I)
SKU_RE = re.compile(r"\b[A-Z]{2}-[A-Z0-9]{2,4}-[A-Z0-9]{2,4}-(?:\d{4}|NV)-\d{3,4}(?:X\d+)?\b")
ZIP_RE = re.compile(r"\b(\d{5})\b")

REASON_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("broken_on_arrival", re.compile(r"\b(broken|smashed|shattered|cracked)\b", re.I)),
    ("damaged_in_transit", re.compile(r"\b(damaged|dented|crushed)\b", re.I)),
    ("leaking", re.compile(r"\b(leak|leaking|leaked|seeping)\b", re.I)),
    ("corked_or_flawed", re.compile(r"\b(corked|tastes? (off|bad|weird|like vinegar|like wet cardboard)|"
                                    r"oxidi[sz]ed|faulty|spoiled|vinegar|flat)\b", re.I)),
    ("wrong_item", re.compile(r"\b(wrong (item|bottle|wine|vintage|product)|not what i ordered|different wine)\b",
                              re.I)),
    ("missing_item", re.compile(r"\b(missing|never (got|received|arrived)|didn'?t (get|receive))\b", re.I)),
    ("late_delivery", re.compile(r"\b(late|delayed|took too long)\b", re.I)),
    ("change_of_mind", re.compile(r"\b(changed my mind|don'?t (want|need|like)|unopened|no longer need|"
                                  r"bought too (much|many))\b", re.I)),
]
ACTION_RE = re.compile(
    r"\b(i want (a |my )?(refund|money back)|refund (me|it|my order|the order)|please (refund|cancel|process|"
    r"go ahead|return)|process (the|my|a) (refund|return)|issue (a |the )?refund|start (a |the )?return|"
    r"cancel (my|the|this) order|i want to (cancel|return)|give me (a|my) refund)\b", re.I)
AFFIRM_RE = re.compile(r"^\s*(yes|yeah|yep|yup|sure|ok(ay)?|confirm(ed)?|go ahead|do it|please do|correct|"
                       r"that'?s (right|fine|correct)|sounds good|approved?)\b", re.I)
NEGATE_RE = re.compile(r"\b(no|nope|don'?t|do not|cancel that|stop|wait|never ?mind|not now|hold on)\b", re.I)

RULES: list[tuple[str, float, re.Pattern]] = [
    ("compliance.crisis", 0.95, re.compile(r"\b(suicid\w*|kill myself|self[- ]harm|hurt myself|end my life)\b", re.I)),
    ("compliance.underage", 0.9, re.compile(r"\b(i'?m|i am)\s+(1[0-9]|20)\b|\bunder\s*21\b|\bunderage\b|"
                                            r"\bfor my (son|daughter|kid|child)\b.*\b(buy|order)\b", re.I)),
    ("human.request", 0.9, re.compile(r"\b(talk|speak|chat) (to|with) (a |an )?(human|person|agent|someone|"
                                      r"representative|manager)\b|\breal person\b", re.I)),
    ("order.cancel", 0.9, re.compile(r"\bcancel\w*\b", re.I)),
    ("refund.status", 0.88, re.compile(r"\b(where('?s| is) my refund|refund (status|rejected|denied|declined|"
                                       r"pending)|why (was|is|did) my (refund|claim)|haven'?t (got|received) "
                                       r"(my|the) refund|status of my (refund|claim|return))\b", re.I)),
    ("policy.returns_refunds", 0.85, re.compile(r"\b(what('?s| is) your (refund|return)s? polic(y|ies)|"
                                                r"(refund|return)s? polic(y|ies)|how do (refunds|returns) work)\b",
                                                re.I)),
    ("claim.wrong_or_missing", 0.86, re.compile(r"\b(wrong (item|bottle|wine|vintage|product)|missing (item|"
                                                r"bottle)|not what i ordered|received the wrong)\b", re.I)),
    ("claim.damaged", 0.86, re.compile(r"\b(broken|smashed|shattered|cracked|damaged|leak\w*)\b", re.I)),
    ("claim.flawed_wine", 0.84, re.compile(r"\b(corked|tastes? (off|bad|weird)|oxidi[sz]ed|faulty|vinegar)\b",
                                           re.I)),
    ("return.change_of_mind", 0.8, re.compile(r"\b(return|send back)\b", re.I)),
    ("refund.request", 0.82, re.compile(r"\b(refund|money back|reimburse\w*)\b", re.I)),
    ("order.status", 0.86, re.compile(r"\b(where('?s| is) my (order|package|wine|delivery)|order status|track\w*|"
                                      r"when (will|does) (it|my order) (arrive|come)|status of (my|the) order|"
                                      r"latest order|delivery status|has (it|my order) shipped)\b", re.I)),
    ("payment.invoice", 0.82, re.compile(r"\b(invoice|receipt|charged|charge on|payment|paid with)\b", re.I)),
    ("loyalty.balance", 0.82, re.compile(r"\b(points|rewards?|loyalty|store credit|account (summary|balance))\b",
                                         re.I)),
    ("delivery.eligibility", 0.82, re.compile(r"\b(deliver\w*|ship\w*) to\b|\bdelivery (fee|options?|time)|"
                                              r"\bshipping (cost|fee|options?)\b|\bdo you (deliver|ship)\b", re.I)),
    ("store.info", 0.85, re.compile(r"\b(store hours|open(ing)? hours|what time (do you|does the store|does it|"
                                    r"is the store) (open|close)|when (do you|does the store) (open|close)|"
                                    r"are you open|address of (the|your) store|holiday hours)\b", re.I)),
    ("account.update_profile", 0.7, re.compile(r"\b(my (address|addresses|profile|email|phone))\b", re.I)),
    ("recommend.by_taste", 0.75, re.compile(r"\b(recommend|suggest|looking for|do you (have|carry|sell)|"
                                            r"what (wines?|products?) do you (sell|have)|bottle of|gift|pair\w* "
                                            r"with|red|white|ros[eé]|champagne|prosecco|sparkling|organic|"
                                            r"non-?alcoholic|cabernet|pinot|chardonnay|sauvignon|malbec|riesling)\b",
                                            re.I)),
    ("chitchat", 0.8, re.compile(r"^\s*(hi|hello|hey|thanks?( you)?|thank you|good (morning|evening))\W*$", re.I)),
]


@dataclass
class Intent:
    name: str
    confidence: float
    entities: dict = field(default_factory=dict)
    secondary: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"name": self.name, "confidence": self.confidence, "entities": self.entities,
                "secondary": self.secondary}


def extract_entities(text: str) -> dict:
    ents: dict = {}
    if orders := [f"WA-{m}" for m in ORDER_RE.findall(text)]:
        ents["order_ids"] = list(dict.fromkeys(orders))
    if rmas := [f"RMA-{m}" for m in RMA_RE.findall(text)]:
        ents["rma_numbers"] = rmas
    if tickets := [f"TKT-{m}" for m in TICKET_RE.findall(text)]:
        ents["ticket_numbers"] = tickets
    if skus := SKU_RE.findall(text.upper()):
        ents["skus"] = skus
    zips = [z for z in ZIP_RE.findall(text) if not any(z in o for o in ents.get("order_ids", []))]
    if zips:
        ents["postal_code"] = zips[0]
    for code, pattern in REASON_PATTERNS:
        if pattern.search(text):
            ents["reason_code"] = code
            break
    if re.search(r"\bstore credit\b", text, re.I):
        ents["refund_method"] = "store_credit"
    if re.search(r"\b(new york|ny|manhattan|brooklyn|chelsea)\b", text, re.I):
        ents["location"] = "NY"
    elif re.search(r"\b(new jersey|nj|hoboken|jersey city)\b", text, re.I):
        ents["location"] = "NJ"
    if ACTION_RE.search(text):
        ents["wants_action"] = True
    return ents


def classify(text: str) -> Intent:
    entities = extract_entities(text)
    matches = [(name, conf) for name, conf, pattern in RULES if pattern.search(text)]
    if not matches:
        if entities.get("order_ids"):
            return Intent("order.status", 0.6, entities)
        return Intent("general.question", 0.45, entities)
    primary, conf = matches[0]
    # "return" + a defect reason is a claim, not change of mind
    if primary == "return.change_of_mind" and entities.get("reason_code") not in (None, "change_of_mind"):
        primary = {"wrong_item": "claim.wrong_or_missing", "missing_item": "claim.wrong_or_missing",
                   "corked_or_flawed": "claim.flawed_wine"}.get(entities["reason_code"], "claim.damaged")
    if primary == "refund.request" and entities.get("reason_code"):
        conf = 0.88
    secondary = [m[0] for m in matches[1:3] if m[0] != primary]
    return Intent(primary, conf, entities, secondary)


def is_affirmative(text: str) -> bool:
    return bool(AFFIRM_RE.search(text)) and not re.search(r"\b(no|not|don'?t)\b", text, re.I)


def is_negative(text: str) -> bool:
    return bool(NEGATE_RE.search(text)) and not AFFIRM_RE.search(text)
