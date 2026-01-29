"""Parse unified diff format using unidiff."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from unidiff import PatchSet


class FileStatus(Enum):
    """Status of a file in the diff."""
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"


@dataclass
class ChangedLine:
    """A single changed line in a diff."""
    line_number: int  # Line number in the target (new) file
    is_addition: bool  # True for additions, False for deletions


@dataclass
class FileChange:
    """Represents changes to a single file."""
    path: Path
    status: FileStatus
    changed_lines: list[ChangedLine]
    added_line_numbers: set[int]  # Lines added in new version
    deleted_line_numbers: set[int]  # Lines deleted from old version


def parse_diff(diff_text: str) -> list[FileChange]:
    """Parse unified diff text into structured file changes.

    Args:
        diff_text: Raw unified diff output from git

    Returns:
        List of FileChange objects representing each changed file
    """
    if not diff_text.strip():
        return []

    patch_set = PatchSet(diff_text)
    changes = []

    for patched_file in patch_set:
        # Determine file status
        if patched_file.is_added_file:
            status = FileStatus.ADDED
        elif patched_file.is_removed_file:
            status = FileStatus.DELETED
        else:
            status = FileStatus.MODIFIED

        # Get file path (use target path for modified/added, source for deleted)
        if status == FileStatus.DELETED:
            path = Path(patched_file.source_file.lstrip("a/"))
        else:
            path = Path(patched_file.target_file.lstrip("b/"))

        changed_lines = []
        added_lines = set()
        deleted_lines = set()

        for hunk in patched_file:
            for line in hunk:
                if line.is_added:
                    line_num = line.target_line_no
                    changed_lines.append(ChangedLine(line_number=line_num, is_addition=True))
                    added_lines.add(line_num)
                elif line.is_removed:
                    line_num = line.source_line_no
                    changed_lines.append(ChangedLine(line_number=line_num, is_addition=False))
                    deleted_lines.add(line_num)

        changes.append(FileChange(
            path=path,
            status=status,
            changed_lines=changed_lines,
            added_line_numbers=added_lines,
            deleted_line_numbers=deleted_lines,
        ))

    return changes
