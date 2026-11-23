"""Knowledge Base retrieval over _KB/**/*.md.

Each document's YAML frontmatter (id, title, category, intents, priority,
status, last_reviewed) becomes chunk metadata; bodies are split at `## `
headings. Retrieval is BM25 with small boosts for title/section matches,
intent match and document priority. It is dependency-free and deterministic;
the `Retriever` protocol allows swapping in a vector store (pgvector,
OpenSearch) without touching the agent."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import structlog

log = structlog.get_logger(__name__)

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")
STOPWORDS = frozenset(
    "a an and are as at be been but by can could do does for from had has have how i if in into is it its "
    "me my of on or our so than that the their them then there these they this to was we were what when "
    "where which who why will with would you your yours about any".split()
)
EXCLUDED_FILES = {"kb-authoring-and-maintenance-standards.md", "research-references.md", "README.md",
                  "tool-reference.md",
                  "brand-profile-template.md"}
PRIORITY_BOOST = {"critical": 1.15, "high": 1.05}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Line-based `key: value` parser, same rules as scripts/validate_kb.py (the KB
    frontmatter is not strict YAML: titles may contain colons)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta, text[end + 5 :]


def as_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [x.strip().strip('"').strip("'") for x in value[1:-1].split(",") if x.strip()]
    return [value] if value else []


_SUFFIXES = ("ations", "ation", "ions", "ion", "ings", "ing", "ed", "es", "s")


def stem(word: str) -> str:
    """Tiny suffix stripper: refunds/refunded -> refund, rejected/rejection -> reject."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


@dataclass
class KBChunk:
    chunk_id: str
    doc_id: str
    title: str
    section: str
    text: str
    category: str
    intents: list[str]
    priority: str
    last_reviewed: str | None
    path: str
    tokens: Counter = field(repr=False, default_factory=Counter)
    length: int = 0


@dataclass
class KBHit:
    doc_id: str
    title: str
    section: str
    text: str
    score: float
    category: str
    last_reviewed: str | None
    path: str

    def as_dict(self, max_chars: int = 1500) -> dict:
        text = self.text if len(self.text) <= max_chars else self.text[:max_chars].rsplit(" ", 1)[0] + " …"
        return {"id": self.doc_id, "title": self.title, "section": self.section, "text": text,
                "score": round(self.score, 3), "last_reviewed": self.last_reviewed}


class Retriever(Protocol):
    def search(self, query: str, *, top_k: int = 4, category: str | None = None,
               intent: str | None = None) -> list[KBHit]: ...


class KnowledgeBase:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.chunks: list[KBChunk] = []
        self.doc_count = 0
        self._df: Counter = Counter()
        self._avgdl = 1.0

    # ------------------------------------------------------------------ loading
    @classmethod
    def load(cls, root: Path) -> KnowledgeBase:
        kb = cls(root)
        if not root.exists():
            log.warning("kb_missing", path=str(root))
            return kb
        for path in sorted(root.rglob("*.md")):
            if path.name in EXCLUDED_FILES:
                continue
            kb._add_document(path)
        kb._index()
        log.info("kb_loaded", documents=kb.doc_count, chunks=len(kb.chunks))
        return kb

    def _add_document(self, path: Path) -> None:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("status") in ("retired", "deprecated"):
            return
        doc_id = meta.get("id") or path.stem
        title = meta.get("title") or path.stem
        last_reviewed = meta.get("last_reviewed") or None
        intents = as_list(meta.get("intents", ""))
        sections = re.split(r"(?m)^## ", body)
        intro = sections[0].strip()
        parts = []
        if intro:
            parts.append(("Overview", re.sub(r"(?m)^# .*$", "", intro).strip()))
        for sec in sections[1:]:
            heading, _, text = sec.partition("\n")
            parts.append((heading.strip(), text.strip()))
        self.doc_count += 1
        for i, (heading, text) in enumerate(parts):
            if len(text) < 40:
                continue
            # title and heading count twice: they are strong relevance signals
            tokens = Counter(tokenize(f"{title} {title} {heading} {heading} {text}"))
            self.chunks.append(KBChunk(
                chunk_id=f"{doc_id}#{i}", doc_id=doc_id, title=title, section=heading, text=text,
                category=str(meta.get("category", "")), intents=intents, priority=str(meta.get("priority", "")),
                last_reviewed=last_reviewed, path=str(path.relative_to(self.root.parent)), tokens=tokens,
                length=sum(tokens.values()),
            ))

    def _index(self) -> None:
        self._df = Counter()
        for c in self.chunks:
            self._df.update(set(c.tokens))
        self._avgdl = sum(c.length for c in self.chunks) / max(len(self.chunks), 1)

    # ------------------------------------------------------------------ search
    def search(self, query: str, *, top_k: int = 4, category: str | None = None,
               intent: str | None = None) -> list[KBHit]:
        q = tokenize(query)
        if not q or not self.chunks:
            return []
        n = len(self.chunks)
        k1, b = 1.5, 0.75
        scored: list[tuple[float, KBChunk]] = []
        for c in self.chunks:
            if category and c.category != category:
                continue
            s = 0.0
            for t in q:
                tf = c.tokens.get(t)
                if not tf:
                    continue
                idf = math.log(1 + (n - self._df[t] + 0.5) / (self._df[t] + 0.5))
                s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * c.length / self._avgdl))
            if s <= 0:
                continue
            if intent and (intent in c.intents or intent.split(".")[0] in {i.split(".")[0] for i in c.intents}):
                s *= 1.25
            s *= PRIORITY_BOOST.get(c.priority, 1.0)
            scored.append((s, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        hits, per_doc = [], Counter()
        for s, c in scored:
            if per_doc[c.doc_id] >= 2:  # diversity: at most two sections per document
                continue
            per_doc[c.doc_id] += 1
            hits.append(KBHit(c.doc_id, c.title, c.section, c.text, s, c.category, c.last_reviewed, c.path))
            if len(hits) >= top_k:
                break
        return hits

    def stats(self) -> dict:
        return {"documents": self.doc_count, "chunks": len(self.chunks)}
