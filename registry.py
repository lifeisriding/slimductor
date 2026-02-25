#!/usr/bin/env python3
"""Claude Code session registry — multi-instance coordination.

Writes a JSON file to ~/.claude/active/ on register, deletes it on deregister.
Uses PID liveness to detect stale entries automatically.

Usage:
    registry.py register              # claim a slot (idempotent)
    registry.py deregister            # release slot
    registry.py list                  # show all active sessions as JSON
    registry.py check                 # human-readable summary

Called automatically by SessionStart and Stop hooks in settings.json.
Can also be run manually: py ~/.claude/registry.py check
"""
import json, os, sys, time
from pathlib import Path

ACTIVE_DIR = Path.home() / ".claude" / "active"
STALE_HOURS = 4


def is_alive(pid: int) -> bool:
    """Check if a PID is still running. Works on Windows and Unix."""
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_INFORMATION = 0x0400
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def session_file() -> Path:
    # Prefer CLAUDE_SESSION_ID (unique UUID per session).
    # Fall back to parent PID — hooks run as subprocesses, so os.getppid()
    # gives Claude Code's own PID, which is consistent across all hook calls
    # for the same session. Never use os.getpid() — it changes per invocation.
    sid = os.environ.get("CLAUDE_SESSION_ID") or f"pid-{os.getppid()}"
    return ACTIVE_DIR / f"{sid}.json"


def register(role: str = "orchestrator") -> None:
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    f = session_file()
    if f.exists():
        return  # Already registered — idempotent
    # Store parent PID (Claude Code's PID) for liveness checking.
    # Hook subprocesses die immediately after running — tracking their PID
    # would make every session appear stale. The parent is Claude Code itself.
    tracking_pid = os.getppid() if os.getppid() > 1 else os.getpid()
    f.write_text(json.dumps({
        "pid": tracking_pid,
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sessionId": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        "cwd": os.getcwd(),
        "role": role,
    }, indent=2))


def deregister() -> None:
    session_file().unlink(missing_ok=True)


def active_sessions() -> list:
    if not ACTIVE_DIR.exists():
        return []
    sessions = []
    for f in ACTIVE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            started = data.get("startedAt", "")
            age_hours = 0
            if started:
                t = time.mktime(time.strptime(started, "%Y-%m-%dT%H:%M:%SZ"))
                age_hours = (time.time() - t) / 3600
            if is_alive(data.get("pid", 0)) and age_hours < STALE_HOURS:
                sessions.append(data)
            else:
                f.unlink(missing_ok=True)  # Auto-clean stale entries
        except Exception:
            pass
    return sessions


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "register"
    try:
        if cmd == "register":
            register()
        elif cmd == "deregister":
            deregister()
        elif cmd == "list":
            print(json.dumps(active_sessions(), indent=2))
        elif cmd == "check":
            sessions = active_sessions()
            orchestrators = [s for s in sessions if s.get("role") == "orchestrator"]
            print(f"{len(sessions)} active session(s), {len(orchestrators)} orchestrator(s)")
            for s in sessions:
                print(f"  [{s['role']}] PID {s['pid']}  {s['cwd']}")
    except Exception:
        pass  # Silent fail — never block Claude Code
