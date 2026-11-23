# Wines AI Platform Agent

An agentic customer-support backend for a licensed online wine retailer with one store in New Jersey and one in New York. Built with FastAPI, Pydantic v2, SQLAlchemy 2 (async), PostgreSQL, LangGraph and Claude.

The agent answers customer questions by combining two sources:
- the **Knowledge Base** ([`_KB/`](_KB/README.md): 14 domain folders, ~90 policy and wine documents)
- the **database** ([`_DB/`](_DB/README.md)), which it reaches **only through typed, authenticated REST Tool APIs**, never by SQL

| Doc | What's in it |
|---|---|
| [docs/API_DESIGN.md](docs/API_DESIGN.md) | Phase 1 design: both API categories, every endpoint, how they communicate, the agent workflow |
| [docs/SAMPLE_REQUESTS.md](docs/SAMPLE_REQUESTS.md) | Real requests and responses, including the refund confirmation flow and its trace |
| [_DB/README.md](_DB/README.md) | Data model, integrity rules and seed scenarios |
| [_KB/00_system/](_KB/00_system/) | Agent policies, the assumptions register (A-xx) and the tool contract |

## Architecture

```
Frontend ──customer JWT──▶ Agentic APIs (/api/v1/agent/*)
                              │  AgentService: session, run, delegated agent JWT
                              ▼
                     LangGraph workflow ──▶ Knowledge Base (BM25, in-process)
                              │
                     ToolExecutor ──HTTP + delegated JWT──▶ Tool APIs (/api/v1/customers, /orders, …)
                     (timeouts, retries,                     routers ▶ services ▶ repositories ▶ PostgreSQL
                      circuit breaker)                       (ownership, policy engine, idempotency, audit)
```

```
app/
  main.py            FastAPI factory: middleware, routers, exception handlers
  container.py       composition root (DI): engine, KB, tool client, agent service
  core/              config, JWT auth, errors, structured logging, masking/redaction,
                     money, rate limiting, request IDs, retry + circuit breaker
  db/                declarative base + portable types, async session, seed loader
  models/            SQLAlchemy models (business tables + agent observability)
  repositories/      every SQL query (no business logic)
  services/          business rules: policy engine (refund/return/cancel), refunds,
                     returns, cancellations, orders, catalog, stores, support, idempotency
  schemas/           Pydantic request/response models (= the response filter)
  api/v1/            routers: HTTP only (customers, orders, business, agent)
  agent/             graph.py (LangGraph), service.py, intent.py, guardrails.py,
                     prompts.py, tracing.py, kb/, llm/ (Claude + rule-based), tools/
migrations/          Alembic (0001: schema + PostgreSQL append-only triggers)
scripts/             initialize_db.py (SQLite reference build), load_seed.py, validate_kb.py
tests/               unit/, api/, agent/ + the phase-2A database tests
```

## Key design decisions

1. **The agent touches data only through HTTP Tool APIs.** Each tool is a Pydantic-typed wrapper around one endpoint. Every chat run mints a short-lived **delegated agent token** (`role=agent`, bound to one customer, session and run). The Tool APIs enforce ownership (returning 404, not 403, so records can't be enumerated) exactly as they do for the customer. The customer ID is **never an LLM parameter**: tools bind it from the session, so a prompt injection can't point a tool at someone else's data.
2. **Same process today, separate tiers tomorrow.** With `TOOL_API_BASE_URL` empty, tool calls go through an in-process ASGI transport: full HTTP stack, no network hop. Set the variable to split the agent and tool tiers into separately scaled deployments.
3. **Asking about a refund never issues one.** `check_refund_eligibility` is a read-only policy decision. `request_refund`, `create_return_request` and `cancel_order` are **gated**: when the LLM calls one, it only records a `pending_action`. The action runs on the next turn, and only on explicit confirmation (a `confirm_action_id` from a button, or an unambiguous "yes"). It then runs **deterministically, without the LLM**, with `Idempotency-Key = action_id`. Any other reply discards it.
4. **The server re-checks everything.** Write endpoints re-run the policy engine and **compute the amount themselves**; the client never sends one. They also enforce the A-60 $150 agent limit (as a service rule *and* a database `CHECK`), evidence and second-claim reviews (A-62), chargeback blocks (RF-R5), NJ/NY rules (A-34/A-35) and windows (A-30–A-32). Anything above the agent's authority returns `202 pending_approval` and opens a P2 ticket.
5. **The policy engine is pure functions** over a loaded order (`services/policy.py`), with every rule citing its KB ID. That makes it unit-testable and lets the eligibility endpoints and write endpoints share one source of truth.
6. **Claude chooses the tools; a deterministic planner is the fallback.** With `ANTHROPIC_API_KEY` set, Claude (`claude-opus-5-5`, effort `medium`) picks tools turn by turn through the official `anthropic` SDK, with parallel tool calls and server-side refusal fallbacks. The stable system prompt and tool list are prompt-cached, and per-turn facts go in a `<context>` block. Without a key, or if Claude is unavailable mid-run, a rule-based planner implements the same interface, so the service still works (in degraded mode) and the whole graph is testable offline.
7. **Observability without chain of thought.** Each run records structured events (guardrail, intent, confirmation check, LLM call, decision, KB retrieval, tool call, action gated/executed, response, error) and per-tool HTTP metadata. Everything stored is PII-redacted: no JWTs, prompts or model thinking.
8. **Money is decimal strings at the API and integer cents in the database.** No floats anywhere.

## Run it

### Option A: Docker (PostgreSQL + Redis + API)

```bash
docker compose up --build            # API on :8000; override ports with API_PORT=8010 DB_PORT=55433
open http://localhost:8000/docs      # OpenAPI / Swagger UI
```
The `migrate` service runs `alembic upgrade head` and then loads the fictional seed (only if the database is empty). To use Claude, export `ANTHROPIC_API_KEY` before `docker compose up`.

### Option B: local Python

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
cp .env.example .env                  # point DATABASE_URL at your PostgreSQL
python scripts/initialize_db.py --force   # (re)build the SQLite reference seed _DB/ecommerce.db
alembic upgrade head                  # create the schema in PostgreSQL
python scripts/load_seed.py           # copy the fictional seed into PostgreSQL
uvicorn app.main:app --reload
```
For a database-free quick look: `python scripts/load_seed.py --database-url sqlite+aiosqlite:///./local.db --recreate`, then run with `DATABASE_URL=sqlite+aiosqlite:///./local.db`.

### Try it

```bash
B=http://localhost:8000/api/v1
TOKEN=$(curl -s -X POST $B/auth/dev-token -H 'Content-Type: application/json' \
  -d '{"role":"customer","subject":"C-100005"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -X POST $B/agent/chat -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100005","session_id":"SESSION1001","message":"Can I get a refund for my order?"}'
```
Seed customers run `C-100001`…`C-100012`, and each one maps to a scenario in [_DB/README.md](_DB/README.md) (split shipment, chargeback, NY order, fraud hold and so on). Staff tokens: `{"role":"staff","subject":"S-1001"}`.

## Tests

```bash
pytest                                                    # 160 tests on SQLite copies of the seed (~10 s)
docker run -d --name pg -e POSTGRES_USER=wines -e POSTGRES_PASSWORD=wines -e POSTGRES_DB=wines_agent \
  -p 55432:5432 postgres:17-alpine
TEST_DATABASE_URL=postgresql+asyncpg://wines:wines@localhost:55432/wines_agent pytest   # same suite on PostgreSQL
ruff check app tests
```

| Suite | What it covers |
|---|---|
| `tests/unit` | money, masking/redaction, JWT, circuit breaker and retry, intent routing for every row of the requirement table, KB retrieval, tool contract (no customer parameter; writes are gated), guardrails |
| `tests/api` | auth and ownership (404 for other customers), response filtering, pagination/filter/sort, error envelope, rate limiting, audit rows, every refund/return/cancellation rule above, idempotent replay and key reuse, the $150 limit going to approval, chargeback block |
| `tests/agent` | each scenario end to end: an "is it refundable?" question creates no refund; an explicit request is gated and executes only on "yes" or a button; decline and unrelated replies discard the action; a second "yes" can't refund twice; compliance blocks; observability endpoints; traces contain no secrets; a scripted Claude-style tool loop with parallel results; LLM outage falling back to the rule-based planner |
| `tests/test_database.py` | the original 36 database constraint tests |

## Environment variables

Everything is in [.env.example](.env.example). The important ones:

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://…` | SQLite (`sqlite+aiosqlite://`) works for local experiments and tests |
| `JWT_SECRET` | dev value | **Must** be set in production (startup fails otherwise) |
| `ENABLE_DEV_AUTH` | `true` | **Must** be `false` in production (startup fails otherwise) |
| `REFERENCE_NOW` | empty | Freezes the clock (demos/tests use `2026-11-19T18:00:00Z`) |
| `ANTHROPIC_API_KEY` | empty | Enables Claude; without it the rule-based planner runs |
| `ANTHROPIC_MODEL` / `ANTHROPIC_EFFORT` | `claude-opus-5-5` / `medium` | |
| `TOOL_API_BASE_URL` | empty | Empty = in-process; set it to split the tiers |
| `RATE_LIMIT_BACKEND` | `memory` | Use `redis` with more than one replica |

## Production notes

- **Scaling.** API pods are stateless: sessions, runs, pending actions and idempotency records live in PostgreSQL, and rate limits live in Redis. Run several replicas behind a load balancer.
- **Database.** Use Alembic only (`--recreate` refuses to run in production). Migration `0001` adds append-only triggers for the audit log, status history, tracking events, ticket messages and the store-credit, gift-card and loyalty ledgers. It also adds a guard that lets a *pending* payment transaction change only its outcome. Next steps: grant the app role `INSERT`-only on `audit_logs`, and partition audit and tracking tables by month.
- **Identity.** `POST /auth/dev-token` exists for local demos only. In production, customer and staff tokens come from your identity provider: switch `JWT_ALGORITHM` to RS256 and verify against the provider's JWKS.
- **Payments.** `SimulatedPaymentGateway` stands in for the processor behind the `PaymentGateway` interface; card data never passes through this service.

## Known limitations

- The **Claude path is covered by a scripted LLM in tests but was not run against the live API here** (no API key was available in this environment). Run a few chats with `ANTHROPIC_API_KEY` set and check `/agent/runs/{id}/steps` before relying on it.
- The rule-based planner is a fallback: for a claim it refunds every eligible unit (after showing the amount and asking for confirmation) instead of asking which bottle. Claude selects specific lines.
- KB retrieval is BM25 (deterministic, no embeddings). The `Retriever` protocol is where a vector store would plug in.
- Not implemented yet (they are in the KB tool contract): cart, promotions/promo-code validation, address and profile updates, loyalty redemption, OTP identity verification, privacy requests, and the staff refund-approval endpoint.
- Business values (fees, windows, the $150 limit) are the KB's **unconfirmed assumptions** A-xx. Change them in the register first (see `_KB/00_system/business-profile-and-assumptions.md`), then here and in the DB `CHECK`s.
