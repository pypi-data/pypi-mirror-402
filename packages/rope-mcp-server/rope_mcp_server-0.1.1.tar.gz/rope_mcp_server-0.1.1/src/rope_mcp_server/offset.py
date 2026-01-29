"""AST-based offset calculation for finding symbols in Python files."""

import ast
from dataclasses import dataclass
from typing import List, Literal


@dataclass
class SymbolInfo:
    """Information about a Python symbol."""

    name: str
    type: Literal["class", "function", "variable"]
    line: int
    col_offset: int
    byte_offset: int


def _line_col_to_offset(content: str, line: int, col: int) -> int:
    """Convert 1-based line and 0-based column to byte offset.

    Args:
        content: File content
        line: 1-based line number
        col: 0-based column offset

    Returns:
        Byte offset into the content
    """
    lines = content.split("\n")
    offset = sum(len(line) + 1 for line in lines[: line - 1])
    return offset + col


def find_symbol_offset(
    content: str,
    symbol_name: str,
    symbol_type: Literal["class", "function", "any"] = "any",
) -> int:
    """Find the byte offset of a symbol in Python source code.

    The offset points to the start of the symbol name (not the 'def'/'class' keyword).

    Args:
        content: Python source code
        symbol_name: Name of the symbol to find
        symbol_type: Type filter - "class", "function", or "any"

    Returns:
        Byte offset pointing to the symbol name

    Raises:
        ValueError: If symbol not found
    """
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and symbol_type in ("class", "any"):
            if node.name == symbol_name:
                # node.col_offset points to 'class', we need to offset to the name
                line_content = content.split("\n")[node.lineno - 1]
                # Find the actual position of the class name in the line
                name_col = line_content.find(symbol_name, node.col_offset)
                if name_col == -1:
                    name_col = node.col_offset + len("class ")
                return _line_col_to_offset(content, node.lineno, name_col)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and symbol_type in (
            "function",
            "any",
        ):
            if node.name == symbol_name:
                line_content = content.split("\n")[node.lineno - 1]
                # Find the actual position of the function name in the line
                name_col = line_content.find(symbol_name, node.col_offset)
                if name_col == -1:
                    # Fallback: after 'def ' or 'async def '
                    keyword = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                    name_col = node.col_offset + len(keyword)
                return _line_col_to_offset(content, node.lineno, name_col)

    raise ValueError(f"Symbol '{symbol_name}' of type '{symbol_type}' not found")


def list_top_level_symbols(content: str) -> List[SymbolInfo]:
    """List all top-level symbols in Python source code.

    Returns classes, functions, and module-level variable assignments.

    Args:
        content: Python source code

    Returns:
        List of SymbolInfo objects
    """
    tree = ast.parse(content)
    symbols = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            line_content = content.split("\n")[node.lineno - 1]
            name_col = line_content.find(node.name, node.col_offset)
            if name_col == -1:
                name_col = node.col_offset + len("class ")
            byte_offset = _line_col_to_offset(content, node.lineno, name_col)
            symbols.append(
                SymbolInfo(
                    name=node.name,
                    type="class",
                    line=node.lineno,
                    col_offset=name_col,
                    byte_offset=byte_offset,
                )
            )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_content = content.split("\n")[node.lineno - 1]
            name_col = line_content.find(node.name, node.col_offset)
            if name_col == -1:
                keyword = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                name_col = node.col_offset + len(keyword)
            byte_offset = _line_col_to_offset(content, node.lineno, name_col)
            symbols.append(
                SymbolInfo(
                    name=node.name,
                    type="function",
                    line=node.lineno,
                    col_offset=name_col,
                    byte_offset=byte_offset,
                )
            )

        elif isinstance(node, ast.Assign):
            # Module-level variable assignments
            for target in node.targets:
                if isinstance(target, ast.Name):
                    byte_offset = _line_col_to_offset(content, node.lineno, target.col_offset)
                    symbols.append(
                        SymbolInfo(
                            name=target.id,
                            type="variable",
                            line=node.lineno,
                            col_offset=target.col_offset,
                            byte_offset=byte_offset,
                        )
                    )

        elif isinstance(node, ast.AnnAssign) and node.target:
            # Annotated assignments like: foo: int = 5
            if isinstance(node.target, ast.Name):
                byte_offset = _line_col_to_offset(content, node.lineno, node.target.col_offset)
                symbols.append(
                    SymbolInfo(
                        name=node.target.id,
                        type="variable",
                        line=node.lineno,
                        col_offset=node.target.col_offset,
                        byte_offset=byte_offset,
                    )
                )

    return symbols


def line_col_to_offset(content: str, line: int, col: int) -> int:
    """Public wrapper for line/column to offset conversion.

    Args:
        content: File content
        line: 1-based line number
        col: 0-based column offset

    Returns:
        Byte offset into the content
    """
    return _line_col_to_offset(content, line, col)
