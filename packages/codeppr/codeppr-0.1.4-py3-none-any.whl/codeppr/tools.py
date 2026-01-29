import click
import subprocess
from pathlib import Path
import stat
import sys
import os
import re
from codeppr.state import read_state, needs_review
from codeppr.git_helper import get_binary_files, is_non_code_file, get_diff_file
from codeppr.configure import set_default_config

HUNK_RE = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

def check_git_repository():
    try:
        # Check if the current directory is a git repository
        subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    
def is_interactive():
    return sys.stdout.isatty()
    
HOOK_NAME = "pre-commit"
HOOK_HEADER = "# Managed by codeppr"

HOOK_BODY = """# Managed by codeppr

# Skip if codeppr is not installed
command -v codeppr >/dev/null 2>&1 || exit 0

# Run codeppr review
codeppr run

# codeppr end
""".strip()
    
def install_pre_commit_hook():
    if not check_git_repository():
        click.echo("Not a git repository. Skipping hook installation.")
        return
    
    # Locate the .git directory
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--git-dir"],
        text=True
    ).strip()

    hooks_dir = Path(git_dir) / "hooks"
    hook_path = hooks_dir / HOOK_NAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle existing hook
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8", errors="ignore")
        if '#!/bin/sh' not in existing:
            # Ensure shebang for shell scripts
            existing = "#!/bin/sh\n" + existing.lstrip()
        if HOOK_HEADER in existing:
            # Replace old codeppr block with new one
            pattern = re.escape(HOOK_HEADER) + r".*?" + re.escape("# codeppr end")
            updated = re.sub(pattern, HOOK_BODY, existing, flags=re.DOTALL)
            hook_path.write_text(updated, encoding="utf-8")
        else:
            # Existing user hook → append safely
            merged = (
                existing.rstrip()
                + "\n\n"
                + HOOK_BODY
            )
            hook_path.write_text(merged, encoding="utf-8")
    else:
        # Create new hook
        hook_path.write_text('#!/bin/sh\n' + HOOK_BODY, encoding="utf-8")

    set_default_config()

    #Ensure executable bit
    make_executable(hook_path)

def make_executable(path: Path):
    """
    Ensure file is executable on Unix systems.
    """
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        # Never fail install due to chmod issues
        pass
    
def check_installed():
    if not check_git_repository():
        return False
    
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--git-dir"],
        text=True
    ).strip()

    hook_path = Path(git_dir) / "hooks" / HOOK_NAME

    if not hook_path.exists():
        return False

    existing = hook_path.read_text(encoding="utf-8", errors="ignore")
    return HOOK_HEADER in existing

def uninstall_pre_commit_hook():
    if not check_git_repository():
        click.echo("Not a git repository. Skipping hook uninstallation.")
        return
    
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--git-dir"],
        text=True
    ).strip()

    hook_path = Path(git_dir) / "hooks" / HOOK_NAME

    if not hook_path.exists():
        return RuntimeError("Pre-commit hook does not exist.")

    existing = hook_path.read_text(encoding="utf-8", errors="ignore")
    if HOOK_HEADER in existing:
        # Remove codeppr block
        pattern = re.escape(HOOK_HEADER) + r".*?" + re.escape("# codeppr end")
        updated = re.sub(pattern, "", existing, flags=re.DOTALL).strip()
        if updated and updated != "#!/bin/sh":
            hook_path.write_text(updated, encoding="utf-8")
        else:
            hook_path.unlink()
    else:
        return RuntimeError("Pre-commit hook not managed by codeppr. Nothing to uninstall.")

def can_prompt() -> bool:
    return os.path.exists("/dev/tty") or os.path.exists("CONIN$")

def input_from_tty(prompt: str) -> str:
    """
    Get input from the controlling terminal (tty) directly.
    This allows prompting even when stdin is redirected.
    """
    if os.name == 'nt':
        # Windows
        tty = open("CONIN$", "r")
    else:
        # Unix-like
        tty = open("/dev/tty", "r")
    
    print(prompt, end="", flush=True)
    return tty.readline().strip()

def separate_staged_files(lines: list[str]):
    valid_files = []
    non_valid_files = []

    binary_files = get_binary_files()
    state = read_state()
    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]  # handles renames safely

        if status == 'D' or path in binary_files or is_non_code_file(path):
            non_valid_files.append({
                "status": status,
                "path": path,
                "change_type": None
            })
            continue

        # If the file has been reviewed and not changed
        diff = get_diff_file(path)
        review_required, was_reviewed_before = needs_review(state, path, diff)
        if not review_required:
            non_valid_files.append({
                "status": status,
                "path": path,
                "change_type": "Not Changed" if was_reviewed_before else None
            })
            continue

        valid_files.append({
            "status": status,
            "path": path,
            "change_type": "Changed" if was_reviewed_before else None
        })

    return valid_files, non_valid_files

def build_diff_line_map(diff: str) -> dict[str, int]:
    """
    Maps added diff lines (starting with '+') to absolute
    line numbers in the new file.
    """
    mapping = {}
    current_new_line = None

    for line in diff.splitlines():
        # New hunk
        if line.startswith("@@"):
            match = HUNK_RE.search(line)
            if match:
                current_new_line = int(match.group(1))
            continue

        if current_new_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            mapping[line] = current_new_line
            current_new_line += 1
        elif line.startswith(" "):
            current_new_line += 1
        elif line.startswith("-"):
            pass  # removed lines don't advance new-file counter

    return mapping