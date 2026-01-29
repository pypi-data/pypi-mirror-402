"""JSON schema and serialization for diff output."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .ast_mapper import ASTNode
from .diff_parser import FileChange, FileStatus
from .git import DiffMode


@dataclass
class ChangeOutput:
    """JSON-serializable change record."""
    type: str
    name: str
    line_start: int
    line_end: int
    change_type: str
    diff_lines: list[int]
    parent: str | None
    signature: str
    content: str


@dataclass
class FileOutput:
    """JSON-serializable file record."""
    path: str
    language: str | None
    status: str
    changes: list[ChangeOutput]


@dataclass
class DiffOutput:
    """JSON-serializable diff output."""
    diff_type: str
    base_ref: str | None
    target_ref: str | None
    files: list[FileOutput]


def create_change_output(node: ASTNode) -> ChangeOutput:
    """Convert an ASTNode to a ChangeOutput."""
    return ChangeOutput(
        type=node.type,
        name=node.name,
        line_start=node.line_start,
        line_end=node.line_end,
        change_type=node.change_type,
        diff_lines=node.diff_lines,
        parent=node.parent,
        signature=node.signature,
        content=node.content,
    )


def create_file_output(
    file_change: FileChange,
    language: str | None,
    ast_nodes: list[ASTNode],
) -> FileOutput:
    """Create a FileOutput from parsed data."""
    return FileOutput(
        path=str(file_change.path),
        language=language,
        status=file_change.status.value,
        changes=[create_change_output(node) for node in ast_nodes],
    )


def create_diff_output(
    diff_mode: DiffMode,
    base_ref: str | None,
    target_ref: str | None,
    files: list[FileOutput],
) -> DiffOutput:
    """Create the final DiffOutput."""
    return DiffOutput(
        diff_type=diff_mode.value,
        base_ref=base_ref,
        target_ref=target_ref,
        files=files,
    )


def serialize_output(output: DiffOutput) -> str:
    """Serialize DiffOutput to JSON string."""
    def to_dict(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        return obj

    return json.dumps(to_dict(output), indent=2)


def write_output(output: DiffOutput, path: Path) -> None:
    """Write DiffOutput to a JSON file."""
    json_str = serialize_output(output)
    path.write_text(json_str)
