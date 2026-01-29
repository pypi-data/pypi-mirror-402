"""Tree-sitter AST parsing and mapping of changed lines to AST nodes."""

from dataclasses import dataclass

from .languages import LanguageInfo


@dataclass
class ASTNode:
    """Represents an AST node containing changed code."""
    type: str  # e.g., "function", "class", "method"
    name: str
    line_start: int
    line_end: int
    change_type: str  # "modified", "added", "deleted"
    diff_lines: list[int]  # Specific changed lines within this node
    parent: str | None  # Parent node name (e.g., class name for a method)
    signature: str  # Function/class signature
    content: str  # Full source code of the node


def _get_node_name(node, language: str) -> str:
    """Extract the name from an AST node."""
    # Different languages have different ways of naming nodes
    name_node = None

    # Try common patterns for finding the name
    for child in node.children:
        if child.type == "identifier":
            name_node = child
            break
        elif child.type == "name":
            name_node = child
            break
        elif child.type == "property_identifier":
            name_node = child
            break
        # For TypeScript/JavaScript classes and interfaces
        elif child.type == "type_identifier":
            name_node = child
            break
        # For TypeScript/JavaScript function expressions in variable declarations
        elif child.type == "variable_declarator":
            for subchild in child.children:
                if subchild.type in ("identifier", "name"):
                    name_node = subchild
                    break

    if name_node:
        return name_node.text.decode("utf-8")

    return "<anonymous>"


def _get_signature(node, source_bytes: bytes, language: str) -> str:
    """Extract the signature of a function/class/method."""
    # For functions, get the first line up to the opening brace or colon
    start_byte = node.start_byte
    end_byte = node.end_byte

    # Get the full node text
    node_text = source_bytes[start_byte:end_byte].decode("utf-8")

    # Find the end of the signature
    lines = node_text.split("\n")
    if not lines:
        return ""

    # For Python, signature ends at the colon
    if language == "python":
        sig_parts = []
        for line in lines:
            sig_parts.append(line)
            if line.rstrip().endswith(":"):
                break
        return "\n".join(sig_parts)

    # For C-like languages, signature ends at the opening brace
    first_line = lines[0]

    # Check if brace is on first line
    if "{" in first_line:
        return first_line.split("{")[0].strip()

    # Otherwise, collect lines until we find a brace
    sig_parts = [first_line]
    for line in lines[1:]:
        if "{" in line:
            sig_parts.append(line.split("{")[0].strip())
            break
        sig_parts.append(line)
        if len(sig_parts) > 5:  # Limit signature length
            break

    return "\n".join(sig_parts)


def _get_parent_name(node) -> str | None:
    """Get the name of the parent class/struct if this is a method."""
    parent = node.parent
    while parent:
        # Check for class-like constructs (not module which is root in Python)
        if parent.type in (
            "class_definition", "class_declaration", "class_specifier",
            "struct_specifier", "impl_item",
        ):
            name = _get_node_name(parent, "")
            # Only return if we found a real name
            if name != "<anonymous>":
                return name
        parent = parent.parent
    return None


def _categorize_node_type(node_type: str, lang_info: LanguageInfo) -> str | None:
    """Categorize a tree-sitter node type into our simplified types."""
    for category, types in lang_info.node_types.items():
        if node_type in types:
            return category
    return None


def _find_containing_nodes(
    node,
    changed_lines: set[int],
    source_bytes: bytes,
    lang_info: LanguageInfo,
    results: list[ASTNode],
    seen_ranges: set[tuple[int, int]],
) -> None:
    """Recursively find AST nodes that contain changed lines."""
    # tree-sitter uses 0-based line numbers, we use 1-based
    node_start_line = node.start_point[0] + 1
    node_end_line = node.end_point[0] + 1

    # Check if this node overlaps with any changed lines
    node_lines = set(range(node_start_line, node_end_line + 1))
    overlapping_lines = node_lines & changed_lines

    if not overlapping_lines:
        return

    # Check if this is a node type we care about
    category = _categorize_node_type(node.type, lang_info)

    if category:
        # Avoid duplicate nodes with the same range
        range_key = (node_start_line, node_end_line)
        if range_key not in seen_ranges:
            seen_ranges.add(range_key)

            name = _get_node_name(node, lang_info.name)
            signature = _get_signature(node, source_bytes, lang_info.name)
            parent = _get_parent_name(node)

            # Get full content of the node
            content = source_bytes[node.start_byte:node.end_byte].decode("utf-8")

            # If this is a method (function inside a class), mark it as such
            if category == "function" and parent:
                category = "method"

            results.append(ASTNode(
                type=category,
                name=name,
                line_start=node_start_line,
                line_end=node_end_line,
                change_type="modified",  # Will be refined later
                diff_lines=sorted(overlapping_lines),
                parent=parent,
                signature=signature,
                content=content,
            ))

    # Recurse into children to find more specific nodes
    for child in node.children:
        _find_containing_nodes(child, changed_lines, source_bytes, lang_info, results, seen_ranges)


def map_changes_to_ast(
    source_code: str,
    changed_lines: set[int],
    lang_info: LanguageInfo,
) -> list[ASTNode]:
    """Map changed lines to AST nodes.

    Args:
        source_code: The full source code of the file
        changed_lines: Set of line numbers that have changed (1-based)
        lang_info: Language information including parser

    Returns:
        List of ASTNode objects representing changed code constructs
    """
    if not source_code or not changed_lines:
        return []

    source_bytes = source_code.encode("utf-8")
    tree = lang_info.parser.parse(source_bytes)

    results: list[ASTNode] = []
    seen_ranges: set[tuple[int, int]] = set()

    _find_containing_nodes(
        tree.root_node,
        changed_lines,
        source_bytes,
        lang_info,
        results,
        seen_ranges,
    )

    # Sort by line number
    results.sort(key=lambda n: n.line_start)

    # Remove nodes that are completely contained within other nodes
    # Keep only the most specific (innermost) nodes
    filtered_results: list[ASTNode] = []
    for node in results:
        is_contained = False
        for other in results:
            if node is other:
                continue
            # Check if node is completely inside other
            if (other.line_start <= node.line_start and
                node.line_end <= other.line_end and
                (other.line_start < node.line_start or node.line_end < other.line_end)):
                # node is contained within other, but we want to keep the innermost
                # So we check if node contains other's diff lines
                if set(node.diff_lines) == set(other.diff_lines) & set(node.diff_lines):
                    is_contained = True
                    break

        if not is_contained:
            filtered_results.append(node)

    return results  # Return all nodes, let output layer decide granularity
