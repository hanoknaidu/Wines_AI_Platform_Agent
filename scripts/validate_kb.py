#!/usr/bin/env python3
"""Validate the _KB knowledge base for the Wines AI Platform Agent.

Checks every Markdown file for:
  * frontmatter presence, required fields and allowed values
  * document ID format, uniqueness and folder prefix
  * `related` IDs that resolve to real documents
  * assumption IDs (A-xx) defined in the assumptions register, and declared in
    `depends_on_assumptions` when used in the text
  * tools named in frontmatter that exist in 00_system/tool-reference.md
  * intents named in frontmatter that exist in 00_system/intent-taxonomy.md
  * relative Markdown links that resolve
  * every document listed in the root README index
  * overdue reviews (last_reviewed + review_cycle_days < today)
  * policy/workflow documents with escalation and example sections
  * secrets / personal data that should never be in a KB

Usage:
  python3 scripts/validate_kb.py                 # validates ../_KB relative to this script
  python3 scripts/validate_kb.py path/to/_KB
  python3 scripts/validate_kb.py --strict        # warnings also fail the run
  python3 scripts/validate_kb.py --json          # machine-readable output (CI)
  python3 scripts/validate_kb.py --today 2027-03-01

Exit codes: 0 = passed, 1 = errors (or warnings with --strict), 2 = bad input.
Standard library only; no dependencies.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass, field

REQUIRED_FIELDS = [
    "id", "title", "category", "subcategory", "doc_type", "intents", "tools",
    "jurisdictions", "audience", "priority", "version", "last_reviewed",
    "review_cycle_days", "owner", "status",
]
ALLOWED = {
    "doc_type": {"policy", "workflow", "guide", "faq", "reference", "index", "template"},
    "priority": {"critical", "high", "medium", "low"},
    "status": {"active", "draft", "draft-contract", "deprecated"},
}
ALLOWED_JURISDICTIONS = {"NJ", "NY", "US"}

# Folder -> expected ID prefix (KB-<PREFIX>-NNN).
FOLDER_PREFIX = {
    "00_system": "SYS",
    "01_wine-by-taste": "TST",
    "02_wine-by-region": "REG",
    "03_wine-by-brand": "BRD",
    "04_sparkling-champagne-prosecco": "SPK",
    "05_low-calorie-and-better-for-you": "LCW",
    "06_organic-biodynamic-natural": "ORG",
    "07_non-alcoholic-wines": "NAW",
    "08_pricing": "PRC",
    "09_stock-and-availability": "STK",
    "10_discounts-and-promotions": "DSC",
    "11_orders-delivery-pickup": "ORD",
    "12_returns-refunds-damages": "RTN",
    "13_account-management": "ACC",
    "14_general-faqs": "FAQ",
}

REGISTER = "00_system/business-profile-and-assumptions.md"
TOOL_REF = "00_system/tool-reference.md"
TAXONOMY = "00_system/intent-taxonomy.md"
ROOT_README = "README.md"

ID_RE = re.compile(r"^KB-([A-Z]+)-(\d{3})$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ASSUMPTION_RE = re.compile(r"\bA-\d+b?\b")
LINK_RE = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")

SECRET_PATTERNS = {
    "Anthropic API key": re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),
    "generic API key": re.compile(r"(?i)\b(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    "card number": re.compile(r"\b(?:\d[ -]?){15,16}\b"),
    "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|edu|org|net|io)\b"),
}


@dataclass
class Doc:
    rel: str
    fm: dict[str, str]
    body: str
    text: str


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm: dict[str, str] = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, text[end + 5:]


def as_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [x.strip().strip('"').strip("'") for x in value[1:-1].split(",") if x.strip()]
    return [value] if value else []


def assumption_key(a: str) -> tuple[int, str]:
    m = re.match(r"A-(\d+)(b?)", a)
    return (int(m.group(1)), m.group(2)) if m else (0, a)


def load_docs(root: str, report: Report) -> dict[str, Doc]:
    docs: dict[str, Doc] = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            parsed = parse_frontmatter(text)
            if not parsed:
                report.err(f"{rel}: missing or invalid frontmatter")
                continue
            fm, body = parsed
            docs[rel] = Doc(rel, fm, body, text)
    return docs


def check_fields(docs: dict[str, Doc], report: Report) -> None:
    for d in docs.values():
        for k in REQUIRED_FIELDS:
            if k not in d.fm or d.fm[k] == "":
                report.err(f"{d.rel}: missing field '{k}'")
        for k, allowed in ALLOWED.items():
            v = d.fm.get(k)
            if v and v not in allowed:
                report.err(f"{d.rel}: {k} '{v}' not in {sorted(allowed)}")
        if d.fm.get("version") and not SEMVER_RE.match(d.fm["version"]):
            report.err(f"{d.rel}: version '{d.fm['version']}' is not semver (x.y.z)")
        try:
            dt.date.fromisoformat(d.fm.get("last_reviewed", ""))
        except ValueError:
            report.err(f"{d.rel}: last_reviewed '{d.fm.get('last_reviewed')}' is not YYYY-MM-DD")
        if not d.fm.get("review_cycle_days", "").isdigit():
            report.err(f"{d.rel}: review_cycle_days must be an integer")
        bad_j = set(as_list(d.fm.get("jurisdictions", ""))) - ALLOWED_JURISDICTIONS
        if bad_j:
            report.err(f"{d.rel}: unknown jurisdictions {sorted(bad_j)}")


def check_ids(docs: dict[str, Doc], report: Report) -> dict[str, str]:
    ids: dict[str, str] = {}
    for d in docs.values():
        doc_id = d.fm.get("id", "")
        if doc_id in ids:
            report.err(f"duplicate id {doc_id}: {d.rel} and {ids[doc_id]}")
        ids[doc_id] = d.rel
        if d.rel == ROOT_README:
            continue
        m = ID_RE.match(doc_id)
        if not m:
            report.err(f"{d.rel}: id '{doc_id}' doesn't match KB-<PREFIX>-NNN")
            continue
        folder = d.rel.split("/")[0]
        expected = FOLDER_PREFIX.get(folder)
        if expected and m.group(1) != expected:
            report.err(f"{d.rel}: id prefix {m.group(1)} should be {expected} for {folder}/")
        if d.rel.endswith("/README.md") and m.group(2) != "000":
            report.warn(f"{d.rel}: folder README ids should end in -000")
    for d in docs.values():
        for r in as_list(d.fm.get("related", "")):
            if r not in ids:
                report.err(f"{d.rel}: related id {r} not found")
    return ids


def check_assumptions(root: str, docs: dict[str, Doc], report: Report) -> set[str]:
    reg_path = os.path.join(root, REGISTER)
    if not os.path.exists(reg_path):
        report.err(f"assumptions register missing: {REGISTER}")
        return set()
    with open(reg_path, encoding="utf-8") as fh:
        defined = set(re.findall(r"^\| (A-\d+b?) \|", fh.read(), re.M))
    for d in docs.values():
        used = set(ASSUMPTION_RE.findall(d.text))
        declared = set(as_list(d.fm.get("depends_on_assumptions", "")))
        for a in sorted(used | declared, key=assumption_key):
            if a not in defined:
                report.err(f"{d.rel}: assumption {a} is not defined in the register")
        if d.rel != REGISTER:
            missing = sorted(used - declared, key=assumption_key)
            if missing:
                report.warn(f"{d.rel}: uses {missing} but doesn't list them in depends_on_assumptions")
    return defined


def check_tools_and_intents(root: str, docs: dict[str, Doc], report: Report) -> None:
    with open(os.path.join(root, TOOL_REF), encoding="utf-8") as fh:
        tools = set(re.findall(r"`([a-z_]+)`", fh.read()))
    with open(os.path.join(root, TAXONOMY), encoding="utf-8") as fh:
        intents = set(re.findall(r"`([a-z_]+\.[a-z_]+|chitchat|out_of_scope)`", fh.read()))
    for d in docs.values():
        for t in as_list(d.fm.get("tools", "")):
            if t != "*" and t not in tools:
                report.err(f"{d.rel}: tool '{t}' is not in {TOOL_REF}")
        for i in as_list(d.fm.get("intents", "")):
            if i != "*" and i not in intents:
                report.warn(f"{d.rel}: intent '{i}' is not in {TAXONOMY}")


def check_links(root: str, docs: dict[str, Doc], report: Report) -> None:
    for d in docs.values():
        for link in LINK_RE.findall(d.body):
            if link.startswith(("http://", "https://")):
                continue
            target = os.path.normpath(os.path.join(root, os.path.dirname(d.rel), link))
            if not os.path.exists(target):
                report.err(f"{d.rel}: broken link {link}")


def check_root_index(docs: dict[str, Doc], report: Report) -> None:
    root = docs.get(ROOT_README)
    if not root:
        report.err("root README.md is missing")
        return
    for rel in docs:
        if rel != ROOT_README and f"]({rel})" not in root.body:
            report.warn(f"root README index doesn't list {rel}")


def check_reviews(docs: dict[str, Doc], today: dt.date, report: Report) -> None:
    for d in docs.values():
        try:
            reviewed = dt.date.fromisoformat(d.fm.get("last_reviewed", ""))
            cycle = int(d.fm.get("review_cycle_days", ""))
        except ValueError:
            continue  # already reported by check_fields
        due = reviewed + dt.timedelta(days=cycle)
        if due < today:
            report.warn(f"{d.rel}: review overdue since {due.isoformat()} (owner: {d.fm.get('owner')})")


def check_content(docs: dict[str, Doc], report: Report) -> None:
    for d in docs.values():
        words = len(d.body.split())
        if words < 120:
            report.warn(f"{d.rel}: only {words} words; may be too thin")
        if d.fm.get("doc_type") in {"policy", "workflow"}:
            headings = " ".join(re.findall(r"^#{2,3} .*$", d.body, re.M)).lower()
            if not re.search(r"escalat|exception", headings):
                report.warn(f"{d.rel}: policy/workflow doc has no Escalation section")
            if not re.search(r"example|sample|dialogue", headings):
                report.warn(f"{d.rel}: policy/workflow doc has no response examples section")


def check_secrets(docs: dict[str, Doc], report: Report) -> None:
    allowed_emails = {"noreply@anthropic.com"}
    for d in docs.values():
        for label, pattern in SECRET_PATTERNS.items():
            for m in pattern.finditer(d.text):
                hit = m.group(0)
                if label == "email address" and hit in allowed_emails:
                    continue
                report.err(f"{d.rel}: possible {label} found: '{hit[:12]}…'")


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Validate the _KB knowledge base.")
    ap.add_argument("kb_dir", nargs="?", default=os.path.join(here, "..", "_KB"),
                    help="path to the _KB folder (default: ../_KB next to this script)")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", help="print a JSON report")
    ap.add_argument("--today", default=None, help="override today's date (YYYY-MM-DD) for review checks")
    args = ap.parse_args()

    root = os.path.abspath(args.kb_dir)
    if not os.path.isdir(root):
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    for required in (REGISTER, TOOL_REF, TAXONOMY):
        if not os.path.exists(os.path.join(root, required)):
            print(f"error: {required} not found under {root}", file=sys.stderr)
            return 2
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    report = Report()
    docs = load_docs(root, report)
    check_fields(docs, report)
    check_ids(docs, report)
    defined = check_assumptions(root, docs, report)
    check_tools_and_intents(root, docs, report)
    check_links(root, docs, report)
    check_root_index(docs, report)
    check_reviews(docs, today, report)
    check_content(docs, report)
    check_secrets(docs, report)

    word_counts = sorted((len(d.body.split()), d.rel) for d in docs.values())
    summary = {
        "kb_dir": root,
        "files": len(docs),
        "folders": len({rel.split("/")[0] for rel in docs if "/" in rel}),
        "total_words": sum(w for w, _ in word_counts),
        "assumptions_defined": len(defined),
        "errors": report.errors,
        "warnings": report.warnings,
        "smallest_files": [{"file": r, "words": w} for w, r in word_counts[:5]],
    }
    failed = bool(report.errors) or (args.strict and bool(report.warnings))

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"KB: {root}")
        print(f"Files: {summary['files']} in {summary['folders']} folders · "
              f"{summary['total_words']:,} words · {summary['assumptions_defined']} assumptions defined")
        for label, items in (("ERROR", report.errors), ("WARN", report.warnings)):
            for item in items:
                print(f"  {label}: {item}")
        print(f"Result: {'FAILED' if failed else 'PASSED'} "
              f"({len(report.errors)} errors, {len(report.warnings)} warnings)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
