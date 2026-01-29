"""Language detection and tree-sitter grammar loading."""

from dataclasses import dataclass
from pathlib import Path

import tree_sitter


# Mapping of file extensions to language names
EXTENSION_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Java
    ".java": "java",
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
    # C#
    ".cs": "c_sharp",
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    # Swift
    ".swift": "swift",
    # Scala
    ".scala": "scala",
    # Shell
    ".sh": "bash",
    ".bash": "bash",
    # JSON
    ".json": "json",
    # YAML
    ".yaml": "yaml",
    ".yml": "yaml",
    # TOML
    ".toml": "toml",
    # HTML
    ".html": "html",
    ".htm": "html",
    # CSS
    ".css": "css",
    # SQL
    ".sql": "sql",
    # Markdown
    ".md": "markdown",
    # Lua
    ".lua": "lua",
    # Elixir
    ".ex": "elixir",
    ".exs": "elixir",
    # Haskell
    ".hs": "haskell",
    # OCaml
    ".ml": "ocaml",
    ".mli": "ocaml",
}


# AST node types that represent important code constructs per language
NODE_TYPES: dict[str, dict[str, list[str]]] = {
    "python": {
        "function": ["function_definition"],
        "class": ["class_definition"],
        "method": ["function_definition"],  # Methods are functions inside classes
        "import": ["import_statement", "import_from_statement"],
    },
    "javascript": {
        "function": ["function_declaration", "arrow_function", "function_expression"],
        "class": ["class_declaration"],
        "method": ["method_definition"],
        "import": ["import_statement"],
    },
    "typescript": {
        "function": ["function_declaration", "arrow_function", "function_expression"],
        "class": ["class_declaration"],
        "method": ["method_definition"],
        "import": ["import_statement"],
        "interface": ["interface_declaration"],
        "type": ["type_alias_declaration"],
    },
    "tsx": {
        "function": ["function_declaration", "arrow_function", "function_expression"],
        "class": ["class_declaration"],
        "method": ["method_definition"],
        "import": ["import_statement"],
        "interface": ["interface_declaration"],
        "type": ["type_alias_declaration"],
    },
    "go": {
        "function": ["function_declaration"],
        "method": ["method_declaration"],
        "struct": ["type_declaration"],
        "interface": ["type_declaration"],
        "import": ["import_declaration"],
    },
    "rust": {
        "function": ["function_item"],
        "struct": ["struct_item"],
        "enum": ["enum_item"],
        "impl": ["impl_item"],
        "trait": ["trait_item"],
        "import": ["use_declaration"],
    },
    "java": {
        "function": ["method_declaration"],
        "class": ["class_declaration"],
        "interface": ["interface_declaration"],
        "import": ["import_declaration"],
    },
    "c": {
        "function": ["function_definition"],
        "struct": ["struct_specifier"],
    },
    "cpp": {
        "function": ["function_definition"],
        "class": ["class_specifier"],
        "struct": ["struct_specifier"],
    },
    "ruby": {
        "function": ["method", "singleton_method"],
        "class": ["class"],
        "module": ["module"],
    },
}


def _get_language(language: str):
    """Get tree-sitter language object for the given language name."""
    # Import language-specific modules dynamically
    if language == "python":
        import tree_sitter_python
        return tree_sitter_python.language()
    elif language == "javascript":
        import tree_sitter_javascript
        return tree_sitter_javascript.language()
    elif language == "typescript":
        import tree_sitter_typescript
        return tree_sitter_typescript.language_typescript()
    elif language == "tsx":
        import tree_sitter_typescript
        return tree_sitter_typescript.language_tsx()
    elif language == "go":
        import tree_sitter_go
        return tree_sitter_go.language()
    elif language == "rust":
        import tree_sitter_rust
        return tree_sitter_rust.language()
    else:
        return None


@dataclass
class LanguageInfo:
    """Information about a detected language."""
    name: str
    parser: tree_sitter.Parser
    node_types: dict[str, list[str]]


def detect_language(path: Path) -> str | None:
    """Detect language from file extension.

    Args:
        path: Path to the file

    Returns:
        Language name or None if not detected
    """
    suffix = path.suffix.lower()
    return EXTENSION_MAP.get(suffix)


def get_language_info(language: str) -> LanguageInfo | None:
    """Get language info including parser and node types.

    Args:
        language: Language name

    Returns:
        LanguageInfo or None if language not supported
    """
    try:
        lang_ptr = _get_language(language)
        if lang_ptr is None:
            return None

        # Wrap the PyCapsule with tree_sitter.Language
        lang = tree_sitter.Language(lang_ptr)
        parser = tree_sitter.Parser(lang)
        node_types = NODE_TYPES.get(language, {
            "function": [],
            "class": [],
        })
        return LanguageInfo(
            name=language,
            parser=parser,
            node_types=node_types,
        )
    except Exception:
        return None


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return list(set(EXTENSION_MAP.values()))
