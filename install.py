#!/usr/bin/env python3
"""
Slimductor installer.

Copies files into ~/.claude/ and patches settings.json to add hooks
and enable Agent Teams.

Usage:
    python install.py             # install
    python install.py --uninstall # remove slimductor files
    python install.py --dry-run   # preview changes without writing
"""
import json
import shutil
import sys
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
REPO_DIR = Path(__file__).parent

FILES_TO_COPY = [
    ("registry.py",                          CLAUDE_DIR / "registry.py"),
    ("rules/coordination.md",                CLAUDE_DIR / "rules" / "coordination.md"),
    ("rules/teams.md",                       CLAUDE_DIR / "rules" / "teams.md"),
    ("rules/security.md",                    CLAUDE_DIR / "rules" / "security.md"),
    ("reference/orchestrator-protocol.md",   CLAUDE_DIR / "reference" / "orchestrator-protocol.md"),
]

HOOKS_TO_ADD = {
    "SessionStart": [{"hooks": [{"type": "command", "command": f"py {CLAUDE_DIR}/registry.py register"}]}],
    "Stop":         [{"hooks": [{"type": "command", "command": f"py {CLAUDE_DIR}/registry.py deregister"}]}],
    "SessionEnd":   [{"hooks": [{"type": "command", "command": f"py {CLAUDE_DIR}/registry.py deregister"}]}],
}

ENV_TO_ADD = {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "true",
}


def log(msg: str, dry_run: bool = False):
    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}{msg}")


def copy_files(dry_run: bool = False):
    for src_rel, dst in FILES_TO_COPY:
        src = REPO_DIR / src_rel
        if not src.exists():
            print(f"  WARNING: source not found: {src}")
            continue
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Back up existing file if present
            if dst.exists():
                backup = dst.with_suffix(dst.suffix + ".bak")
                shutil.copy2(dst, backup)
                log(f"  backed up: {dst.name} → {dst.name}.bak")
            shutil.copy2(src, dst)
        log(f"  copied: {src_rel} → {dst}", dry_run)


def patch_settings(dry_run: bool = False):
    settings_path = CLAUDE_DIR / "settings.json"

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            print(f"  ERROR: {settings_path} is not valid JSON. Skipping settings patch.")
            return
    else:
        settings = {}

    changed = False

    # Add env vars
    settings.setdefault("env", {})
    for key, value in ENV_TO_ADD.items():
        if settings["env"].get(key) != value:
            settings["env"][key] = value
            log(f"  settings.json: env.{key} = {value}", dry_run)
            changed = True

    # Add hooks (merge, don't overwrite)
    settings.setdefault("hooks", {})
    for event, hook_list in HOOKS_TO_ADD.items():
        existing = settings["hooks"].get(event, [])
        # Check if our command is already there
        our_command = hook_list[0]["hooks"][0]["command"]
        already_present = any(
            h.get("hooks", [{}])[0].get("command", "") == our_command
            for h in existing
        )
        if not already_present:
            settings["hooks"].setdefault(event, []).extend(hook_list)
            log(f"  settings.json: added {event} hook", dry_run)
            changed = True

    if changed and not dry_run:
        backup = settings_path.with_suffix(".json.bak")
        if settings_path.exists():
            shutil.copy2(settings_path, backup)
            log(f"  backed up: settings.json → settings.json.bak")
        settings_path.write_text(json.dumps(settings, indent=2))
        log("  settings.json updated")
    elif not changed:
        log("  settings.json: already up to date")


def create_active_dir(dry_run: bool = False):
    active_dir = CLAUDE_DIR / "active"
    if not active_dir.exists():
        if not dry_run:
            active_dir.mkdir(parents=True, exist_ok=True)
        log(f"  created: ~/.claude/active/", dry_run)


def uninstall(dry_run: bool = False):
    print("Uninstalling slimductor...")

    for src_rel, dst in FILES_TO_COPY:
        if dst.exists():
            if not dry_run:
                dst.unlink()
            log(f"  removed: {dst}", dry_run)

    # Remove hooks from settings.json
    settings_path = CLAUDE_DIR / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            return

        changed = False
        for event, hook_list in HOOKS_TO_ADD.items():
            our_command = hook_list[0]["hooks"][0]["command"]
            if event in settings.get("hooks", {}):
                before = len(settings["hooks"][event])
                settings["hooks"][event] = [
                    h for h in settings["hooks"][event]
                    if h.get("hooks", [{}])[0].get("command", "") != our_command
                ]
                if len(settings["hooks"][event]) < before:
                    changed = True
                    log(f"  settings.json: removed {event} hook", dry_run)

        for key in ENV_TO_ADD:
            if key in settings.get("env", {}):
                del settings["env"][key]
                changed = True
                log(f"  settings.json: removed env.{key}", dry_run)

        if changed and not dry_run:
            settings_path.write_text(json.dumps(settings, indent=2))

    print("Done. Restart Claude Code to apply changes.")


def install(dry_run: bool = False):
    print(f"Installing slimductor into {CLAUDE_DIR}...")
    copy_files(dry_run)
    create_active_dir(dry_run)
    patch_settings(dry_run)
    print()
    if dry_run:
        print("Dry run complete. No files were written.")
    else:
        print("Done. Restart Claude Code to apply changes.")
        print()
        print("Verify with:")
        print("  py ~/.claude/registry.py check")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if "--uninstall" in sys.argv:
        uninstall(dry_run)
    else:
        install(dry_run)
