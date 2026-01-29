"""Git diff execution module."""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DiffMode(Enum):
    """Type of git diff to perform."""
    STAGED = "staged"
    WORKING = "working"
    COMMITS = "commits"


@dataclass
class DiffResult:
    """Result of a git diff operation."""
    diff_type: DiffMode
    base_ref: str | None
    target_ref: str | None
    diff_text: str
    repo_root: Path


def get_repo_root() -> Path:
    """Get the root directory of the current git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def run_git_diff(
    mode: DiffMode = DiffMode.STAGED,
    from_ref: str | None = None,
    to_ref: str | None = None,
) -> DiffResult:
    """Execute git diff and return the result.

    Args:
        mode: The type of diff to perform
        from_ref: Base reference for commit comparison
        to_ref: Target reference for commit comparison

    Returns:
        DiffResult containing the diff output and metadata
    """
    repo_root = get_repo_root()

    if mode == DiffMode.STAGED:
        cmd = ["git", "diff", "--cached"]
        base_ref = "HEAD"
        target_ref = None
    elif mode == DiffMode.WORKING:
        cmd = ["git", "diff"]
        base_ref = "HEAD"
        target_ref = None
    else:  # COMMITS
        if not from_ref:
            raise ValueError("from_ref is required for commit comparison")
        cmd = ["git", "diff", from_ref]
        if to_ref:
            cmd.append(to_ref)
        base_ref = from_ref
        target_ref = to_ref

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    return DiffResult(
        diff_type=mode,
        base_ref=base_ref,
        target_ref=target_ref,
        diff_text=result.stdout,
        repo_root=repo_root,
    )


def get_file_content(path: Path, ref: str | None = None) -> str | None:
    """Get file content from git or working directory.

    Args:
        path: Path to the file (relative to repo root)
        ref: Git reference to get content from. If None, reads from working directory.

    Returns:
        File content as string, or None if file doesn't exist
    """
    if ref is None:
        # Read from working directory
        repo_root = get_repo_root()
        full_path = repo_root / path
        if full_path.exists():
            return full_path.read_text()
        return None

    # Read from git
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None
