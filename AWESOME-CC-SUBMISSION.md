# Awesome Claude Code Submission Draft

Submit at: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml
**Earliest submit date: March 3, 2026** (one week after first public commit: Feb 24, 2026)

---

## Form Fields

**Display Name**
Slimductor

**Category**
Tooling 🧰

**Sub-Category**
Orchestrators

**Primary Link**
https://github.com/lifeisriding/slimductor

**Author Name**
lifeisriding

**Author Link**
https://github.com/lifeisriding

**License**
MIT

**Description**
Lightweight session registry for running multiple Claude Code instances simultaneously. A SessionStart hook writes a PID file to ~/.claude/active/ when each session opens; SessionEnd cleans it up. Stale entries from crashes are auto-cleaned via PID liveness check on next read. Markdown rules files (loaded automatically as context) tell Claude how to determine its role, delegate work via Task tool, and hand off cleanly at context limits. No servers, no dependencies beyond Python stdlib.

**Validate Claims**
1. Install: `python install.py` (then restart Claude Code)
2. Open two Claude Code terminals
3. In either terminal, run: `py ~/.claude/registry.py check`
4. Expected output: `2 active session(s), 2 orchestrator(s)` with both PIDs listed
5. Close one terminal, run check again — drops to `1 active session(s)` automatically

**Specific Task(s)**
Open two Claude Code terminals after installing. In one, ask Claude to check the session registry and describe what it sees.

**Specific Prompt(s)**
Run `py ~/.claude/registry.py check` and tell me how many sessions are active and what their roles are.

**Additional Comments**
Tested on Windows 11 with Claude Code v2.1.56. Windows required a non-obvious fix: hooks run through py.exe → python.exe before the script, so os.getppid() returned the short-lived launcher PID instead of claude.exe. The fix walks the Win32 process tree (CreateToolhelp32Snapshot) to find the stable parent. Falls back to os.getppid() on macOS/Linux where this isn't an issue.

Also note: Claude Code's Stop hook fires after every agent response, not at session end — only SessionStart and SessionEnd are used.
