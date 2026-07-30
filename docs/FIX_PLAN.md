# Fix Plan — FUTURIST OS branch (pre-merge)

**Status: NOT STARTED.** This is a plan only — no code has been changed as a result of this document. Every item below requires explicit go-ahead before implementation, per Z Master's instruction. Findings are detailed in full in [`AUDIT_REPORT.md`](./AUDIT_REPORT.md).

**Priority tiers:**
- **P0 — Critical.** Merge blocker. Exploitable by any self-registered `member` account, or breaks the security assumption the rest of the code relies on.
- **P1 — High.** Deployment blocker. Won't work as documented, or leaves a real hole even for a trusted single operator.
- **P2 — Medium.** Real but not blocking; track as backlog once P0/P1 are done.

Effort estimates are rough (solo dev, this codebase's style) and assume no scope creep beyond the fix itself.

---

## P0 — Critical (fix before merge)

| ID | Title | File(s) | Fix approach | Effort | Depends on |
|---|---|---|---|---|---|
| F1 | Gate MCP server creation to admin only | `apps/api/app/api/v1/mcp.py` | Add `require_admin` (or equivalent role check) dependency to `create_server` (and any other mutating MCP endpoint). Closes S1's primary attack vector. | S (~1-2h) | — |
| F2 | Strip environment from spawned shells | `apps/api/app/live/terminal_manager.py`, `apps/api/app/orchestrator/tools/terminal.py`, `sandbox.py` | Replace `{**os.environ, ...}` with an explicit minimal allowlist (`PATH`, `HOME`, `TERM`, workspace-scoped vars only). No secret env vars should ever reach a spawned shell. | M (~half day, needs care not to break legitimate tool use of env) | — |
| F3 | Add RBAC + rate limiting to terminal/browser endpoints | `apps/api/app/api/v1/terminal.py`, `apps/api/app/api/v1/browser.py` | Reuse the existing `rate_limiter` dependency from `auth.py`; decide and enforce whether these require `admin` role or just tighter per-user limits, consistent with the "single trusted admin" assumption stated elsewhere in the code. | S–M (~half day) | F1 (same RBAC pattern) |
| F4 | Apply SSRF guard to `read_page` | `apps/api/app/orchestrator/tools/research.py` | Call `is_safe_url` (same as `call_api`) before fetching, and re-check after following each redirect hop (don't just check the initial URL with `follow_redirects=True`). | S (~1-2h) | F7 (fix guard itself first, or guard is still an improvement without it) |
| F5 | Restrict browser `navigate()` to safe schemes/URLs | `apps/api/app/live/browser_manager.py` | Block `file:`, `data:`, `about:` (or restrict `data:` to image types if needed for legitimate use), and route `http(s)://` targets through the same SSRF check as F4. | S–M (~half day, check for legitimate internal use of `about:blank` etc.) | F7 |
| F6 | Apply SSRF guard to MCP `sse` transport | `apps/api/app/mcp/client.py` | Call `is_safe_url` on `server.url` before `sse_client(server.url)`. | S (~1h) | F1, F7 |
| F7 | Fix DNS-rebinding hole in `ssrf_guard.py` | `apps/api/app/orchestrator/tools/ssrf_guard.py` | Resolve the hostname once, validate the IP, then connect to that pinned IP directly (e.g. via `httpx` transport with a custom resolver, or connect-by-IP with `Host` header set) instead of letting the HTTP client re-resolve DNS independently. | M (~half day, this is the trickiest one — needs a real fix, not just a second check) | — |
| F8 | Force required secrets at startup, remove insecure defaults | `apps/api/app/core/config.py` | Remove the literal default for `JWT_SECRET_KEY`; make app startup fail loudly (not just log) if `JWT_SECRET_KEY` or `ENCRYPTION_KEY` is unset/equal to a known placeholder when `ENV=production`. | S (~1-2h) | — |
| F9 | Make `ENCRYPTION_KEY` absence a hard failure, not a silent no-op | `apps/api/app/core/crypto.py` | Same startup-validation approach as F8: if `ENV=production` and `ENCRYPTION_KEY` is unset, refuse to start rather than silently storing plaintext. | S (~1h, can combine with F8's startup check) | F8 |

**P0 total estimate:** ~3-4 focused days including testing, not weeks — this is targeted hardening of an otherwise sound design, not a rearchitecture.

---

## P1 — High (fix before real deployment)

| ID | Title | File(s) | Fix approach | Effort |
|---|---|---|---|---|
| F10 | Serve a real production build of the frontend | `apps/web/Dockerfile`, `infra/docker-compose.yml` | Multi-stage Dockerfile: `vite build` in a build stage, serve `dist/` via a lightweight static server (nginx, or `vite preview`/`serve`) in the runtime stage. Update compose service accordingly. | M (~half day) |
| F11 | Fix Vite host-allowlisting for the documented reverse-proxy setup | `apps/web/vite.config.ts` (dev) or resolved by F10 (prod no longer uses Vite's dev server) | If F10 lands, this mostly resolves itself for prod. For local/dev-behind-proxy use, add `server.allowedHosts` for the specific documented domain(s). | S (~1h, mostly moot after F10) |
| F12 | Decide on Chromium isolation and reconcile docs with reality | `apps/api/app/live/browser_manager.py`, `docs/architecture/FUTURIST_OS_ARCHITECTURE.md`, `infra/docker-compose.yml` | Either (a) actually isolate Playwright/Chromium into a separate worker/container as the architecture doc originally specified, or (b) explicitly update the architecture doc to reflect the current in-process design and document the accepted risk/mitigation (e.g. resource limits on the API container). Don't leave code and doc contradicting each other. | L (~2-3 days if isolating; ~1h if just updating docs to match reality) |
| F13 | Add WebSocket reconnection + safe parsing | `apps/web/src/lib/chat-socket.ts`, `apps/web/src/app/browser/BrowserPage.tsx`, `apps/web/src/app/terminal/TerminalPage.tsx` | Wrap `JSON.parse` in try/catch with a surfaced error state; add `onclose`-triggered reconnect with backoff and a visible "reconnecting..." UI state. | M (~1 day across all three call sites) |

---

## P2 — Medium (backlog once P0/P1 land)

| ID | Title | File(s) | Notes |
|---|---|---|---|
| F14 | Move refresh token out of `localStorage` | `apps/web/src/store/auth-store.ts` | httpOnly cookie for the refresh token closes the XSS-exfiltration path entirely; access token can stay memory-only as-is. |
| F15 | Add refresh-token reuse detection / session-family invalidation | `apps/api/app/api/v1/auth.py` | On detected reuse of an already-rotated token, revoke the entire session family, not just the used token. |
| F16 | Run containers as non-root | `apps/api/Dockerfile`, `apps/web/Dockerfile` | Add `useradd`/`USER` directives. |
| F17 | Fix `restore.sh`'s inaccurate "overwrites completely" claim | `infra/scripts/restore.sh` | Either add `--clean --if-exists` to the dump/restore flow so it actually does what the prompt claims, or correct the prompt text to describe what really happens. |
| F18 | Add an explicit delegation recursion-depth guard | `apps/api/app/orchestrator/tools/delegate.py`, `orchestrator/tool_registry.py` | Track depth in `ToolContext` and cap it in code, not just via seed-data convention. |
| F19 | Accessibility pass on frontend | `apps/web/src/app/**/*.tsx` | `aria-label`s on icon-only controls, live regions for async status, basic keyboard nav check. |
| F20 | Add a React error boundary | `apps/web/src/App.tsx` | Prevent a single page's render exception from white-screening the whole app. |
| F21 | Test coverage: `research.py`, `memory.py`'s `read_memory`, `run_terminal_command` | `apps/api/tests/` | These are exactly the tools most exposed to prompt injection (per S4/S12) and currently have zero tests — should get coverage as part of, not after, the F4/F2 fixes. |
| F22 | Test coverage: success paths for `design`, `automation`/n8n, `marketing.seo_analyze` | `apps/api/tests/` | Currently only negative/error branches are tested for these. |

---

## Suggested execution order

1. F8, F9 (startup validation) — cheapest, and everything else benefits from secrets being guaranteed-real in any test/staging environment.
2. F7 (fix the SSRF guard itself) — do this before F4/F5/F6 so those don't get built on top of a guard that's still bypassable.
3. F1, F2, F3 (RCE + secrets exfiltration + RBAC) — the highest-impact, most directly exploitable group.
4. F4, F5, F6 (apply the now-fixed guard everywhere it's missing).
5. F10, F11, F12 (deployment blockers) — can happen in parallel with the above since it's a different part of the codebase.
6. F13 (frontend resilience).
7. P2 backlog, opportunistically or in a follow-up pass.

**Next step:** awaiting Z Master's go-ahead on which item(s) to actually implement, and on this branch vs. a fresh feature branch off it.
