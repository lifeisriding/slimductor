# Team Design Principles

## Default: Always Delegate
For any non-trivial task, the orchestrator spins up a team via Task tool.
Working inline fills the orchestrator's context fast and misses parallelism.

**Do inline:** single-file edits, quick lookups, yes/no questions.
**Delegate:** research, planning, multi-file changes, verification — anything non-trivial.

---

## Team Patterns (choose autonomously)
| Task type                   | Team structure                                          |
|-----------------------------|---------------------------------------------------------|
| Research + write            | Researcher → Executor                                   |
| Multi-file / subsystem      | One agent per subsystem, all parallel                   |
| Unknown territory           | Parallel researchers → Planner → Parallel executors     |
| Any significant change      | + Verifier agent after execution                        |
| Complex research            | Multiple parallel researchers with different angles     |

## Nested Agents
Subagents may spawn their own sub-agents when scope warrants it:
- Phase agent → Researcher + Executor pair
- Research agent → parallel sub-researchers on independent subtopics

Keep each agent focused on one concern. Depth over breadth per agent.
**Spawn in parallel** when independent. **Sequence** only when output feeds the next.

---

## Use the Right Agent Type
| Job                                | Agent type          |
|------------------------------------|---------------------|
| Find files, search code, explore   | `Explore`           |
| Architecture, strategy, trade-offs | `Plan`              |
| Web research, multi-step tasks     | `general-purpose`   |
| Execute GSD plan with commits      | `gsd-executor`      |
| Review code before merge           | `code-reviewer`     |
| Security issues                    | `security-reviewer` |
| Systematic bug investigation       | `gsd-debugger`      |

---

## Native Agent Teams (Experimental)
Enable with `"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": true` in settings.json.
Team lead = explicit orchestrator. Teammates run in separate context windows with `TeammateIdle`
auto-assigning tasks.
**Caveat:** `/resume` does NOT restore in-process teammates. Shutdown is unreliable.
Best for fresh sessions only — don't use if you'll need to resume.

---

## Orchestrator Context Budget
The orchestrator routes and synthesizes — it doesn't execute.
If the orchestrator is doing heavy work inline, delegate more aggressively.
**Target: orchestrator spends <30% of its turns on direct work.**
