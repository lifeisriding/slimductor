# slimductor

Lightweight orchestration protocol for multi-instance Claude Code sessions.

No servers. No databases. One Python script and a set of rules files.

---

## The Problem

Running multiple Claude Code sessions simultaneously is broken by design:

- Two sessions in the same directory share `.claude/plans/`, chat history, and config — with no file locking ([#27311](https://github.com/anthropics/claude-code/issues/27311), [#7702](https://github.com/anthropics/claude-code/issues/7702))
- Concurrent sessions corrupt `~/.claude.json` credentials ([#961](https://github.com/anthropics/claude-code/issues/961), [#18998](https://github.com/anthropics/claude-code/issues/18998))
- Two sessions in the same folder can mutually freeze ([#13499](https://github.com/anthropics/claude-code/issues/13499))
- No native session lock file exists yet ([#19364](https://github.com/anthropics/claude-code/issues/19364), open Jan 2026)

Slimductor solves this with three things:
1. **Worktree-first** — use `claude --worktree` by default (now native in Claude Code CLI)
2. **Session registry** — a lightweight PID-based registry so sessions know about each other
3. **Orchestrator protocol** — clear rules for role assignment, task delegation, and handover

---

## What It Installs

```
~/.claude/
├── registry.py              # session registry (register, deregister, check, list)
├── rules/
│   ├── coordination.md      # orchestrator rules, handover protocol, file conflict prevention
│   ├── teams.md             # team design patterns, nested agents, agent type guide
│   └── security.md          # tiered security checklist by project type
├── reference/
│   └── orchestrator-protocol.md  # full spec: registry format, TRAFFIC.md, known bugs
└── settings.json            # patched: adds SessionStart/SessionEnd hooks + Agent Teams env var
```

Rules files in `~/.claude/rules/` are automatically loaded into every Claude Code session as context.

---

## Install

```bash
python install.py
```

That's it. Restart Claude Code after installing.

To verify:
```bash
py ~/.claude/registry.py check
```

To uninstall:
```bash
python install.py --uninstall
```

---

## How It Works

### Session Registry
When Claude Code starts, a `SessionStart` hook fires `registry.py register`, writing:
```json
{
  "pid": 12345,
  "startedAt": "2026-02-24T10:00:00Z",
  "sessionId": "abc-123",
  "cwd": "C:/Users/you/my-project",
  "role": "orchestrator"
}
```
to `~/.claude/active/{session-id}.json`.

When Claude Code stops, a `SessionEnd` hook fires `registry.py deregister`, deleting the file.

If Claude Code crashes and the hook doesn't fire, the next session reads the entry, checks whether the PID is still alive, and auto-cleans stale entries. No manual cleanup needed.

### Orchestrator Protocol
The first session to register for a project domain is the orchestrator. Rules files loaded into every session tell Claude how to:
- Check `~/.claude/active/` on startup to determine its role
- Delegate work via Task tool (never work inline for non-trivial tasks)
- Design teams autonomously (researcher → planner → executor pattern)
- Write a `HANDOVER.md` when context approaches 60% and transition cleanly

### Hook Reliability Note
Claude Code hooks have known reliability bugs ([#4362](https://github.com/anthropics/claude-code/issues/4362), [#6305](https://github.com/anthropics/claude-code/issues/6305), [#13193](https://github.com/anthropics/claude-code/issues/13193)). Slimductor treats hooks as a convenience, not a guarantee. The registry uses PID liveness checks so stale entries from missed hooks are auto-cleaned on next read. Claude's coordination rules also instruct it to verify its registration on startup.

---

## Usage

### Starting a session (git projects)
```bash
claude --worktree                    # auto-named worktree
claude --worktree feature-name       # named worktree
```
Each worktree gets its own branch and its own `.claude/` directory, eliminating plan file bleeding and config corruption.

### Check active sessions
```bash
py ~/.claude/registry.py check
# 2 active session(s), 1 orchestrator(s)
#   [orchestrator] PID 1234  C:/Users/you/my-project
#   [worker]       PID 5678  C:/Users/you/my-project
```

### Shared task list across terminals
```bash
# Set in every terminal that should share tasks
export CLAUDE_CODE_TASK_LIST_ID=my-project
```

### Agent Teams (experimental)
Slimductor enables `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=true` by default. The team lead session is the explicit orchestrator; teammates run in their own context windows.
> **Note:** `/resume` doesn't restore in-process teammates. Use for fresh sessions only.

---

## Philosophy

- **Lightweight**: one Python script, three markdown files, no dependencies beyond stdlib
- **Instructions-first**: coordination rules live in markdown that Claude reads — no DSL, no config language
- **Hook-backed, not hook-dependent**: hooks automate the happy path; PID liveness handles the rest
- **Delegate by default**: the orchestrator's job is routing and synthesis, not execution — keeps context small and work parallel
- **Worktrees solve most problems**: `claude --worktree` is the single biggest improvement; everything else is belt-and-suspenders

---

## Files Reference

| File | Purpose |
|---|---|
| `registry.py` | Session registry: register, deregister, list, check |
| `rules/coordination.md` | Role determination, orchestrator rules, handover protocol |
| `rules/teams.md` | Team patterns, nested agents, agent type selection |
| `rules/security.md` | Security checklist scoped by project type |
| `reference/orchestrator-protocol.md` | Registry format, TRAFFIC.md spec, known Claude Code bugs |

---

## Requirements

- Python 3.8+ (stdlib only)
- Claude Code CLI
- Works on Windows, macOS, Linux

---

## License

MIT
