# Orchestrator Protocol — Full Reference

## Registry File Format
Each Claude Code session writes to `~/.claude/active/{SESSION_ID}.json`:

```json
{
  "pid": 12345,
  "startedAt": "2026-02-24T10:00:00Z",
  "sessionId": "abc-123-def",
  "cwd": "C:/Users/marcl/my-project",
  "role": "orchestrator"
}
```

`role` values: `"orchestrator"` | `"worker"` | `"vacating"`

Registry is auto-managed by hooks in `~/.claude/settings.json`:
- `SessionStart` → writes registration
- `Stop` / `SessionEnd` → deletes registration

Hooks are unreliable (known Claude Code bugs: #4362, #6305, #10367, #13193).
If `registry.py check` shows stale entries, delete them manually from `~/.claude/active/`.

Manual registry commands:
```bash
py ~/.claude/registry.py register      # claim slot (idempotent)
py ~/.claude/registry.py deregister    # release slot
py ~/.claude/registry.py check         # human-readable summary
py ~/.claude/registry.py list          # full JSON
```

---

## Orchestrator Determination Algorithm
1. Run `py ~/.claude/registry.py check`
2. If no orchestrator entries for this `cwd` → you are orchestrator
3. If orchestrator entry exists → check if PID is alive (registry.py does this automatically)
4. If orchestrator PID is dead but entry remains → stale, treat as #2
5. If live orchestrator exists in same project → you are a worker, claim task scope in TRAFFIC.md

---

## TRAFFIC.md Format (project-level coordination)
Place in project root. Format:

```markdown
# Traffic Control — {Project Name}

## Active Sessions
| Session | Role | Domain | Branch | Last Update |
|---------|------|--------|--------|-------------|
| S26 | orchestrator | auth module | feature/S26-auth | 2026-02-24 10:30 |
| S27 | worker | dashboard | feature/S27-dash | 2026-02-24 10:45 |

## Claimed Files
| File | Claimed By | Since |
|------|------------|-------|
| app/auth.py | S26 | 10:30 |

## Recent Handoffs
| From | To | Branch | Status |
|------|----|--------|--------|
| S25 | merged | feature/S25-api | ✓ merged 2026-02-23 |
```

---

## Handover Document Template
Write as `HANDOVER.md` in the project root before closing context-full session.

```markdown
# Handover — {Project} — {Date}

## Completed This Session
- [x] Task 1 (file: path/to/file.py, commit: abc123)
- [x] Task 2 ...

## Current State
Brief description of where things stand.

## Next Tasks (ordered)
1. Highest priority next step
2. ...

## Key Decisions Made
- Decision 1: reason
- Decision 2: reason

## Open Questions / Blockers
- Question or blocker for Marc to resolve

## Files Touched
- path/to/file.py — what changed
- path/to/other.py — what changed
```

---

## Shared Task List (Native, Zero-Config)
To share a task list across multiple terminal sessions:
```bash
# Set in every terminal that should share tasks
export CLAUDE_CODE_TASK_LIST_ID=my-project-name
```
Tasks created in any session appear in all sessions. `blockedBy` dependency DAGs work across
sessions — completing a task in Session A auto-unblocks dependent tasks in Session B.

---

## Agent Teams (Experimental)
Enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: true` in `~/.claude/settings.json`.
The team lead is the explicit orchestrator. Teammates run in separate context windows.

**Known limitations (as of Feb 2026):**
- `/resume` does NOT restore in-process teammates
- Shutdown is unreliable
- `TeammateIdle` hook for auto-task-assignment works but `Stop` hook reliability is poor
- Best for fresh sessions only

**To launch a team:** Use the TeammateTool from the team lead session.
Team configs stored in `~/.claude/teams/{team-name}/config.json`.

---

## Starting a New Session (Worktree Pattern)
```bash
# For any git project — this is the default
claude --worktree                        # auto-named worktree
claude --worktree feature-name           # named worktree
claude --worktree feature-name --tmux    # worktree + detached tmux session
```
Each worktree gets its own branch and its own `.claude/` directory.
Eliminates plan file bleeding (Issue #27311), config corruption (Issue #961),
and session freeze bugs (Issue #13499).

---

## Known Claude Code Multi-Instance Bugs (Feb 2026)
- **#961**: `~/.claude.json` has no file locking — concurrent R-M-W causes corruption at 30+ sessions
- **#27311**: `.claude/plans/` shared across sessions in same directory — use worktrees
- **#13499**: Two sessions in same folder can mutually freeze (macOS)
- **#7702**: Sessions in same folder share chat history and bleed tasks
- **#19364**: No native session lock file yet (requested, open)
- **#4362 / #6305 / #10367 / #13193**: Various hook reliability bugs

Worktrees solve most of these. The registry.py approach with PID liveness handles the rest.
