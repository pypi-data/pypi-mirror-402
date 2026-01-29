"""CLI entry point using Click."""

from pathlib import Path

import click

from .ast_mapper import map_changes_to_ast
from .diff_parser import parse_diff, FileStatus
from .git import run_git_diff, get_file_content, DiffMode
from .languages import detect_language, get_language_info
from .output import (
    create_file_output,
    create_diff_output,
    write_output,
    serialize_output,
    FileOutput,
)


@click.command()
@click.option(
    "--working", "-w",
    is_flag=True,
    help="Diff working directory changes (unstaged)",
)
@click.option(
    "--from", "from_ref",
    help="Base commit reference for comparison",
)
@click.option(
    "--to", "to_ref",
    help="Target commit reference for comparison",
)
@click.option(
    "--output", "-o",
    default="diff.json",
    help="Output file path (default: diff.json)",
)
@click.option(
    "--stdout",
    is_flag=True,
    help="Output to stdout instead of file",
)
def main(working: bool, from_ref: str | None, to_ref: str | None, output: str, stdout: bool) -> None:
    """Generate AST-aware diff output for LLM consumption.

    By default, diffs staged changes. Use --working for unstaged changes,
    or --from/--to for commit comparisons.
    """
    # Determine diff mode
    if from_ref:
        mode = DiffMode.COMMITS
    elif working:
        mode = DiffMode.WORKING
    else:
        mode = DiffMode.STAGED

    # Run git diff
    try:
        diff_result = run_git_diff(mode, from_ref, to_ref)
    except Exception as e:
        raise click.ClickException(f"Failed to run git diff: {e}")

    if not diff_result.diff_text.strip():
        click.echo("No changes detected.")
        return

    # Parse diff
    file_changes = parse_diff(diff_result.diff_text)

    if not file_changes:
        click.echo("No file changes parsed.")
        return

    # Process each file
    file_outputs: list[FileOutput] = []

    for file_change in file_changes:
        language = detect_language(file_change.path)
        lang_info = get_language_info(language) if language else None

        ast_nodes = []

        if lang_info and file_change.status != FileStatus.DELETED:
            # Get file content for AST parsing
            source_code = get_file_content(file_change.path)

            if source_code:
                # Map changes to AST nodes
                changed_lines = file_change.added_line_numbers
                ast_nodes = map_changes_to_ast(source_code, changed_lines, lang_info)

                # Set change_type based on file status
                for node in ast_nodes:
                    if file_change.status == FileStatus.ADDED:
                        node.change_type = "added"
                    else:
                        node.change_type = "modified"

        file_output = create_file_output(file_change, language, ast_nodes)
        file_outputs.append(file_output)

    # Create final output
    diff_output = create_diff_output(
        diff_mode=mode,
        base_ref=diff_result.base_ref,
        target_ref=diff_result.target_ref,
        files=file_outputs,
    )

    # Output
    if stdout:
        click.echo(serialize_output(diff_output))
    else:
        output_path = Path(output)
        write_output(diff_output, output_path)
        click.echo(f"Diff output written to {output_path}")


if __name__ == "__main__":
    main()
