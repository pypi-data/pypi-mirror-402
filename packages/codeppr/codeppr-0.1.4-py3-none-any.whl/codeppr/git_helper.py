import subprocess
import click
from pathlib import Path
import hashlib

NON_CODE_EXTENSIONS = {
    # prose / docs
    ".md",
    ".rst",
    ".txt",
    ".toml",

    # data / tables
    ".csv",
    ".tsv",
    ".xlsx",
    ".json",
    ".xml",

    # office-style text
    ".docx",
    ".odt",

    # misc text artifacts
    ".log",
    ".patch",
    ".lock",
    ".gitignore",
    ".gitattributes",
}

def get_staged_files_with_status() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    return result.stdout.splitlines()

def get_binary_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--numstat"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    binaries = set()
    for line in result.stdout.splitlines():
        added, removed, path = line.split("\t")
        if added == "-" and removed == "-":
            binaries.add(path)

    return binaries

def is_non_code_file(path: str) -> bool:
    p = Path(path)
    # Check both suffix and full filename (for dotfiles like .gitignore)
    return p.suffix.lower() in NON_CODE_EXTENSIONS or p.name.lower() in NON_CODE_EXTENSIONS

def get_diff_file(path: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--cached", "--", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout

def get_git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    
    if result.returncode != 0:
        return ""
    
    return result.stdout.strip()

def get_diff_hash(diff) -> str:
    """Return a stable hash of the diff content, even when None/bytes."""
    if diff is None:
        diff = ""
    if isinstance(diff, bytes):
        diff = diff.decode("utf-8", errors="replace")

    return hashlib.sha256(diff.encode("utf-8", errors="replace")).hexdigest()
