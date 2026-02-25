# Security Guidelines

## Identify Your Project Type First
| Type                    | Examples                                    |
|-------------------------|---------------------------------------------|
| **Script / Automation** | invoice downloader, heightmap tools         |
| **Internal Tool**       | matchstick game, local dashboards           |
| **API / Service**       | hidden-factory backend, public endpoints    |

---

## Script / Automation
- [ ] No hardcoded secrets — use env vars or prompt at runtime
- [ ] Credential files (`token.json`, `.env`) excluded from git, deleted when not in use

## Internal Tool (single-user / local)
All of the above, plus:
- [ ] Auth tokens scoped minimally (read-only where possible)
- [ ] Error messages don't expose internal paths

## API / Service (multi-user or public-facing)
All of the above, plus:
- [ ] User inputs validated and sanitized
- [ ] SQL injection: parameterized queries only
- [ ] XSS: sanitize HTML output
- [ ] CSRF protection (session-cookie auth only — not needed for JWT/token auth)
- [ ] Auth + authorization verified on every endpoint
- [ ] Rate limiting on public endpoints
- [ ] Error responses don't leak stack traces or internal structure
- [ ] Run `pip audit` / `npm audit` before release

## AI-Specific Risks (all project types)
- [ ] Don't log raw prompts that may contain PII
- [ ] Sanitize AI-generated content before writing to files or DB
- [ ] Prompt injection: never pass unsanitized external data (web content, user files) directly into prompts

---

## Secret Management
- Never hardcode secrets — use env vars or a secret manager
- Validate secrets are present at startup
- OAuth tokens: delete `token.json` when not in use, never commit

---

## Security Response
1. STOP
2. Use the **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Check codebase for the same pattern elsewhere
