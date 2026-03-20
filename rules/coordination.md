# Multi-Instance Coordination

## Default: Use Worktrees
For any git project, start with `claude --worktree` (or `claude --worktree feature-name`).
Each worktree gets its own branch and its own `.claude/` directory — eliminates plan bleeding,
config corruption, and file conflicts at the OS level. This is the recommended default.

---

## Step 1 — Determine Your Role
Check `~/.claude/active/` for running sessions (auto-populated by SessionStart hook; run
`py ~/.claude/registry.py check` to verify):
- **No active orchestrator for this project** → you are the orchestrator. Verify registration.
- **Active orchestrator listed** → you are a parallel worker. Claim a task scope in TRAFFIC.md.
- **HANDOVER.md present + orchestrator vacated** → read it first, then claim orchestrator role.

**Orchestrator** = Claude instance responsible for the session's direction and task routing.
First instance on a project domain is orchestrator. Multiple terminals = independent orchestrators
of separate domains — each registers separately.

---

## Orchestrator Rules
1. **Delegate via Task tool by default.** Don't do non-trivial work inline — see teams.md.
2. **Verify registration** in `~/.claude/active/` on startup (hook fires automatically; check if it didn't).
3. **Use shared task list** when coordinating across terminals: set `CLAUDE_CODE_TASK_LIST_ID=project-name` in all sessions.
4. **Plan handover at ~60% context** — write HANDOVER.md, update registry, notify Marc.

## Worker / Subagent Rules
- Work only within assigned scope.
- Do NOT modify `~/.claude/active/`, MEMORY.md, CLAUDE.md, or global config unless explicitly assigned.
- Complete your task and return results. No scope creep.
- May spawn sub-agents if scope is complex enough (see teams.md).

---

## File Conflict Prevention
Worktrees eliminate conflicts for project files — use them.
For shared files (TRAFFIC.md, MEMORY.md): check `~/.claude/active/` for active claims before writing.
Two sessions must never write the same non-worktree file simultaneously.

## Circuit Breaker
After 2 failed attempts on the same blocker: stop, explain clearly, ask Marc. Never brute-force.

---

## Handover Protocol
When context reaches ~60%:
1. Confirm all subagents have completed and returned their results.
2. Write `HANDOVER.md` in the project root:
   - What's done (with file paths)
   - Current state and key decisions made
   - Next tasks (ordered by priority)
   - Open questions or blockers
3. Run `py ~/.claude/registry.py deregister` or update role to "vacating" in your registry entry.
4. Tell Marc: "Context at ~60%. HANDOVER.md written. Ready for new session."

Incoming session: read HANDOVER.md before anything else. Run `py ~/.claude/registry.py register`.

---

## Testing Before Finishing
| Change type        | Required                        |
|--------------------|---------------------------------|
| Code changes       | Full relevant test suite        |
| Config / docs only | None required                   |
| Script/automation  | Run against sample data         |

---
*Registry format, TRAFFIC.md spec, hook details: `~/.claude/reference/orchestrator-protocol.md`*
*Hidden-Factory / Docker hub-spoke specifics: `/home/node/.claude/reference/coordination-protocol.md`*
