from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import json
from codeppr.git_helper import get_git_head, get_diff_hash
from typing import Tuple

STATE_DIR = Path(".git/codeppr")
STATE_FILE = STATE_DIR / "codeppr_state.json"
STATE_VERSION = 1

def empty_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "commit_session": {
            "git_head": get_git_head(),
            "started_at": now_iso(),
        },
        "files": {}
    }

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return empty_state()

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        # Corrupt state → reset
        return empty_state()

    # Invalidate if HEAD changed
    if state.get("commit_session", {}).get("git_head") != get_git_head():
        return empty_state()

    return state

def write_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    tmp_file = STATE_FILE.with_suffix(".tmp")

    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    tmp_file.replace(STATE_FILE)

def needs_review(
    state: dict[str, Any],
    path: str,
    current_diff: str,
) -> Tuple[bool, bool]: # returns (needs_review, was_reviewed_before)
    file_state = get_file_state(state, path)
    current_hash = get_diff_hash(current_diff)

    if not file_state:
        return True, False

    changed = file_state.get("diff_hash") == current_hash
    return not changed, True

def get_file_state(state: dict[str, Any], path: str) -> dict | None:
    return state.get("files", {}).get(path)

def update_file_review(
    state: dict[str, Any],
    path: str,
    diff: str,
) -> None:
    state.setdefault("files", {})[path] = {
        "diff_hash": get_diff_hash(diff),
        "reviewed_at": now_iso(),
    }

def clear_state() -> None:
    if STATE_DIR.exists():
        for p in STATE_DIR.iterdir():
            p.unlink()