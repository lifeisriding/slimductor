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


def _win_process_snapshot() -> tuple:
    """Return (pid_to_parent, pid_to_name) maps for all Windows processes."""
    import ctypes
    import ctypes.wintypes

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize",             ctypes.wintypes.DWORD),
            ("cntUsage",           ctypes.wintypes.DWORD),
            ("th32ProcessID",      ctypes.wintypes.DWORD),
            ("th32DefaultHeapID",  ctypes.c_size_t),   # ULONG_PTR — pointer-sized
            ("th32ModuleID",       ctypes.wintypes.DWORD),
            ("cntThreads",         ctypes.wintypes.DWORD),
            ("th32ParentProcessID",ctypes.wintypes.DWORD),
            ("pcPriClassBase",     ctypes.c_long),
            ("dwFlags",            ctypes.wintypes.DWORD),
            ("szExeFile",          ctypes.c_char * 260),
        ]

    TH32CS_SNAPPROCESS = 0x00000002
    snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return {}, {}
    pid_map, name_map = {}, {}
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    try:
        if ctypes.windll.kernel32.Process32First(snap, ctypes.byref(entry)):
            while True:
                pid_map[entry.th32ProcessID] = entry.th32ParentProcessID
                name_map[entry.th32ProcessID] = entry.szExeFile.decode("utf-8", errors="replace").lower()
                if not ctypes.windll.kernel32.Process32Next(snap, ctypes.byref(entry)):
                    break
    finally:
        ctypes.windll.kernel32.CloseHandle(snap)
    return pid_map, name_map


# Process names that are Claude Code itself (the stable session process).
_CLAUDE_EXES = {"claude.exe", "claude"}
# Process names that are short-lived wrappers we want to skip past.
_SKIP_EXES = {"py.exe", "python.exe", "python3", "python", "bash.exe", "bash", "sh.exe", "sh"}


def get_tracking_pid() -> int:
    """Return the long-lived parent PID to use for liveness checking.

    On Unix: os.getppid() is the shell / Claude Code process — correct.
    On Windows: `py script.py` spawns through py.exe and potentially several
    bash.exe subshells before reaching claude.exe.  Walk up the process tree
    until we find claude.exe (preferred) or the first non-skippable ancestor.
    """
    if sys.platform != "win32":
        ppid = os.getppid()
        return ppid if ppid > 1 else os.getpid()
    try:
        pid_map, name_map = _win_process_snapshot()
        pid = os.getpid()
        last_alive = pid
        for _ in range(15):                     # safety cap
            parent = pid_map.get(pid, 0)
            if parent <= 1 or parent == pid:
                break
            pname = name_map.get(parent, "")
            if pname in _CLAUDE_EXES:
                return parent                   # found claude.exe — ideal
            if is_alive(parent):
                last_alive = parent
                if pname not in _SKIP_EXES:
                    break                       # first non-wrapper alive ancestor
            pid = parent
        return last_alive
    except Exception:
        pass
    ppid = os.getppid()
    return ppid if ppid > 1 else os.getpid()


def session_file() -> Path:
    # Prefer CLAUDE_SESSION_ID (unique UUID per session).
    # Fall back to tracking PID — consistent across all hook calls for the
    # same session. On Windows we skip the py.exe launcher layer.
    sid = os.environ.get("CLAUDE_SESSION_ID") or f"pid-{get_tracking_pid()}"
    return ACTIVE_DIR / f"{sid}.json"


def register(role: str = "orchestrator") -> None:
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    f = session_file()
    if f.exists():
        return  # Already registered — idempotent
    # Store the long-lived parent PID (Claude Code / shell) for liveness checking.
    # Hook subprocesses die immediately — tracking their own PID would make
    # every session appear stale.  get_tracking_pid() handles the Windows
    # py.exe launcher layer automatically.
    tracking_pid = get_tracking_pid()
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
