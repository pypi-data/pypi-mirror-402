"""Core refactoring functions (without MCP decorators)."""

import json
import os
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from rope.base.exceptions import RefactoringError
from rope.refactor.extract import ExtractMethod
from rope.refactor.inline import InlineVariable
from rope.refactor.move import MoveModule, create_move
from rope.refactor.rename import Rename

from .offset import find_symbol_offset, line_col_to_offset, list_top_level_symbols
from .rope_utils import (
    close_project,
    create_file_if_not_exists,
    get_changed_files,
    get_project,
    get_resource,
)


def _find_conflicting_files(
    project_path: str,
    module_path: str,
    dest_folder: str,
) -> list[tuple[str, str]]:
    """Find files that import from BOTH the dest package AND the module being moved.

    These files cause Rope to crash with a syntax error during move operations.

    Args:
        project_path: Root directory of the project
        module_path: Path to module being moved (e.g., "app/views/foo_extra.py")
        dest_folder: Destination folder (e.g., "app/views/foo")

    Returns:
        List of (file_path, content) tuples for conflicting files
    """
    project_root = Path(project_path)

    # Convert paths to import patterns
    # module_path: "app/views/foo_extra.py" -> "app.views.foo_extra" or "app/views/foo_extra"
    module_import = module_path.replace("/", ".").replace("\\", ".").rstrip(".py")
    if module_import.endswith(".py"):
        module_import = module_import[:-3]

    # dest_folder: "app/views/foo" or "app/views/foo/" -> "app.views.foo" or "app/views/foo"
    dest_import = dest_folder.rstrip("/").replace("/", ".").replace("\\", ".")

    conflicting_files = []

    for py_file in project_root.rglob("*.py"):
        # Skip the module being moved itself
        rel_path = str(py_file.relative_to(project_root))
        if rel_path == module_path:
            continue

        # Skip files in .ropeproject, __pycache__, etc.
        if any(part.startswith(".") or part == "__pycache__" for part in py_file.parts):
            continue

        try:
            content = py_file.read_text()
        except Exception:
            continue

        # Check if file imports from both places
        has_dest_import = False
        has_module_import = False

        # Patterns to match imports (both "from x import" and "import x")
        # Using both dot and slash notation for safety
        dest_patterns = [
            f"from {dest_import}",
            f"import {dest_import}",
            f"from {dest_folder.rstrip('/')}",
        ]
        module_patterns = [
            f"from {module_import}",
            f"import {module_import}",
        ]

        for pattern in dest_patterns:
            if pattern in content:
                has_dest_import = True
                break

        for pattern in module_patterns:
            if pattern in content:
                has_module_import = True
                break

        if has_dest_import and has_module_import:
            conflicting_files.append((rel_path, content))

    return conflicting_files


@contextmanager
def _hide_conflicting_files(
    project_path: str,
    conflicting_files: list[tuple[str, str]],
) -> Iterator[list[str]]:
    """Temporarily hide files that cause Rope to crash.

    Renames files to .py._rope_hidden, yields control, then restores them.

    Args:
        project_path: Root directory of the project
        conflicting_files: List of (file_path, content) tuples

    Yields:
        List of hidden file paths (relative)
    """
    project_root = Path(project_path)
    hidden_suffix = "._rope_hidden"
    hidden_paths = []

    try:
        # Hide the files
        for rel_path, _ in conflicting_files:
            original = project_root / rel_path
            hidden = project_root / (rel_path + hidden_suffix)
            if original.exists():
                original.rename(hidden)
                hidden_paths.append(rel_path)

        yield hidden_paths

    finally:
        # Restore the files
        for rel_path in hidden_paths:
            hidden = project_root / (rel_path + hidden_suffix)
            original = project_root / rel_path
            if hidden.exists():
                hidden.rename(original)


def _fix_imports_in_file(
    file_path: Path,
    old_import: str,
    new_import: str,
) -> bool:
    """Fix imports in a single file after move operation.

    Handles both absolute and relative imports.

    Args:
        file_path: Path to the file to fix
        old_import: Old import path (e.g., "app.views.foo_extra")
        new_import: New import path (e.g., "app.views.foo.extra")

    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text()
        original_content = content

        # Fix absolute imports
        # "from app.views.foo_extra import X" -> "from app.views.foo.extra import X"
        # "import app.views.foo_extra" -> "import app.views.foo.extra"
        content = content.replace(f"from {old_import} import", f"from {new_import} import")
        content = content.replace(f"import {old_import}", f"import {new_import}")

        # Fix relative imports (for files in the same package)
        # "from .foo_extra import X" -> "from .extra import X"
        old_module_name = old_import.split(".")[-1]  # e.g., "service_contractor_extra"
        new_module_name = new_import.split(".")[-1]  # e.g., "extra"

        if old_module_name != new_module_name:
            # Replace relative imports
            content = content.replace(
                f"from .{old_module_name} import",
                f"from .{new_module_name} import"
            )

        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception:
        return False


def list_symbols(project_path: str, file_path: str) -> str:
    """List all top-level symbols in a Python file.

    Args:
        project_path: Root directory of the Python project
        file_path: File path relative to project_path

    Returns:
        JSON with symbols: [{"name": "Foo", "type": "class", "line": 5, "byte_offset": 42}, ...]
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, file_path)
        content = resource.read()

        symbols = list_top_level_symbols(content)
        return json.dumps(
            {"success": True, "symbols": [asdict(s) for s in symbols]},
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def move_symbol(
    project_path: str,
    source_file: str,
    symbol_name: str,
    dest_file: str,
) -> str:
    """Move a class or function to another file.

    Updates all imports across the project automatically.

    Args:
        project_path: Root directory of the Python project
        source_file: Source file path relative to project_path
        symbol_name: Name of the class or function to move
        dest_file: Destination file path (created if doesn't exist)

    Returns:
        JSON with success status and list of changed files
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, source_file)
        content = resource.read()

        # Find symbol offset
        offset = find_symbol_offset(content, symbol_name)

        # Create destination file if it doesn't exist
        dest_resource = create_file_if_not_exists(project, dest_file)

        # Perform the move
        mover = create_move(project, resource, offset)
        changes = mover.get_changes(dest_resource)
        project.do(changes)

        changed_files = get_changed_files(changes)
        return json.dumps(
            {"success": True, "changed_files": changed_files},
            indent=2,
        )
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def rename_symbol(
    project_path: str,
    file_path: str,
    symbol_name: str,
    new_name: str,
) -> str:
    """Rename a symbol including all references and imports across the project.

    Args:
        project_path: Root directory of the Python project
        file_path: File containing the symbol (relative to project_path)
        symbol_name: Current name of the symbol
        new_name: New name for the symbol

    Returns:
        JSON with success status and list of changed files
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, file_path)
        content = resource.read()

        # Find symbol offset
        offset = find_symbol_offset(content, symbol_name)

        # Perform the rename
        renamer = Rename(project, resource, offset)
        changes = renamer.get_changes(new_name)
        project.do(changes)

        changed_files = get_changed_files(changes)
        return json.dumps(
            {"success": True, "changed_files": changed_files},
            indent=2,
        )
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def extract_method(
    project_path: str,
    file_path: str,
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
    new_name: str,
) -> str:
    """Extract a code region as a new method.

    Args:
        project_path: Root directory of the Python project
        file_path: File path relative to project_path
        start_line: Start line (1-based)
        start_col: Start column (0-based)
        end_line: End line (1-based)
        end_col: End column (0-based)
        new_name: Name for the extracted method

    Returns:
        JSON with success status and list of changed files
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, file_path)
        content = resource.read()

        # Convert line/col to byte offsets
        start_offset = line_col_to_offset(content, start_line, start_col)
        end_offset = line_col_to_offset(content, end_line, end_col)

        # Perform extraction
        extractor = ExtractMethod(project, resource, start_offset, end_offset)
        changes = extractor.get_changes(new_name)
        project.do(changes)

        changed_files = get_changed_files(changes)
        return json.dumps(
            {"success": True, "changed_files": changed_files},
            indent=2,
        )
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def inline_variable(
    project_path: str,
    file_path: str,
    variable_name: str,
    line: int,
) -> str:
    """Inline a variable at all usage sites.

    Args:
        project_path: Root directory of the Python project
        file_path: File path relative to project_path
        variable_name: Name of the variable to inline
        line: Line number where variable is defined (1-based)

    Returns:
        JSON with success status and list of changed files
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, file_path)
        content = resource.read()

        # Find the variable on the specified line
        lines = content.split("\n")
        if line < 1 or line > len(lines):
            raise ValueError(f"Line {line} is out of range")

        line_content = lines[line - 1]
        col = line_content.find(variable_name)
        if col == -1:
            raise ValueError(f"Variable '{variable_name}' not found on line {line}")

        offset = line_col_to_offset(content, line, col)

        # Perform inlining
        inliner = InlineVariable(project, resource, offset)
        changes = inliner.get_changes()
        project.do(changes)

        changed_files = get_changed_files(changes)
        return json.dumps(
            {"success": True, "changed_files": changed_files},
            indent=2,
        )
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def move_module(
    project_path: str,
    module_path: str,
    dest_folder: str,
) -> str:
    """Move a module or package to another folder.

    Updates all imports across the project automatically.

    Args:
        project_path: Root directory of the Python project
        module_path: Path to module file or package folder (relative to project_path)
        dest_folder: Destination folder path (relative to project_path)

    Returns:
        JSON with success status and list of changed files
    """
    try:
        project = get_project(project_path)
        resource = get_resource(project, module_path)

        # Get destination folder resource
        dest_resource = project.get_resource(dest_folder)

        # Perform the move
        mover = MoveModule(project, resource)
        changes = mover.get_changes(dest_resource)
        project.do(changes)

        changed_files = get_changed_files(changes)
        return json.dumps(
            {"success": True, "changed_files": changed_files},
            indent=2,
        )
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def move_and_rename_module(
    project_path: str,
    module_path: str,
    dest_folder: str,
    new_name: str | None = None,
) -> str:
    """Move a module to a folder and optionally rename it.

    This is a two-step operation:
    1. Move module to destination folder
    2. Rename the module (if new_name provided or auto-detected)

    Auto-detection: If module is `foo_bar.py` and dest is `foo/`,
    it will automatically strip the `foo_` prefix → `foo/bar.py`

    Includes workaround for Rope bug: Files that import from BOTH the destination
    package AND the module being moved are temporarily hidden during the move,
    then their imports are fixed manually.

    Example:
        move_and_rename_module(
            "views/service_contractor_extra.py",
            "views/service_contractor/",
            new_name="extra"  # or None for auto-detect
        )
        Result: views/service_contractor/extra.py

    Args:
        project_path: Root directory of the Python project
        module_path: Path to module file (relative to project_path)
        dest_folder: Destination folder path (relative to project_path)
        new_name: New name for the module (without .py), or None to auto-detect

    Returns:
        JSON with success status and list of changed files
    """
    try:
        if not module_path.endswith('.py'):
            raise ValueError(f"module_path must be a .py file, got: {module_path}")

        module_name = os.path.basename(module_path)[:-3]  # Remove .py
        dest_folder_name = os.path.basename(dest_folder.rstrip('/'))

        # Auto-detect new name by stripping destination folder prefix
        if new_name is None:
            prefix = f"{dest_folder_name}_"
            if module_name.startswith(prefix):
                new_name = module_name[len(prefix):]
            else:
                new_name = module_name  # No rename needed

        # Calculate import paths for later fixing
        old_import = module_path.replace("/", ".").replace("\\", ".")
        if old_import.endswith(".py"):
            old_import = old_import[:-3]

        final_module_path = os.path.join(dest_folder, f"{new_name}.py")
        new_import = final_module_path.replace("/", ".").replace("\\", ".")
        if new_import.endswith(".py"):
            new_import = new_import[:-3]

        # Find files that would cause Rope to crash
        conflicting_files = _find_conflicting_files(project_path, module_path, dest_folder)
        manually_fixed_files = []

        # Hide conflicting files, do the move, then restore and fix
        with _hide_conflicting_files(project_path, conflicting_files) as _:
            # Need to get project AFTER hiding files so Rope doesn't see them
            project = get_project(project_path)

            # Step 1: Move module to destination
            resource = get_resource(project, module_path)
            dest_resource = project.get_resource(dest_folder)

            mover = MoveModule(project, resource)
            move_changes = mover.get_changes(dest_resource)
            project.do(move_changes)

            all_changed_files = set(get_changed_files(move_changes))

            # Step 2: Rename if needed
            moved_module_path = os.path.join(dest_folder, f"{module_name}.py")

            if module_name != new_name:
                moved_resource = project.get_resource(moved_module_path)
                renamer = Rename(project, moved_resource, None)
                rename_changes = renamer.get_changes(new_name)
                project.do(rename_changes)

                all_changed_files.update(get_changed_files(rename_changes))
                # Update the path in changed files
                all_changed_files.discard(moved_module_path)
                all_changed_files.add(final_module_path)

        # After context manager exits, files are restored.
        # Now fix imports in the previously hidden files.
        for rel_path, _ in conflicting_files:
            file_path = Path(project_path) / rel_path
            if _fix_imports_in_file(file_path, old_import, new_import):
                manually_fixed_files.append(rel_path)
                all_changed_files.add(rel_path)

        # Remove old module path from changed files
        all_changed_files.discard(module_path)

        result = {
            "success": True,
            "changed_files": sorted(all_changed_files),
            "new_path": final_module_path,
        }

        if manually_fixed_files:
            result["manually_fixed_files"] = manually_fixed_files
            result["note"] = (
                "Some files had conflicting imports and were fixed manually. "
                "Please verify the imports are correct."
            )

        return json.dumps(result, indent=2)
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def convert_module_to_init(
    project_path: str,
    module_path: str,
) -> str:
    """Convert a module file into a package by moving it to __init__.py.

    Transforms `foo.py` into `foo/__init__.py`. No import changes needed
    since the import path stays the same!

    Example:
        `views/customer_order.py` becomes `views/customer_order/__init__.py`
        Import `from views.customer_order import X` stays unchanged.

    This is the recommended way to convert a module to a package when you
    want to later split it into multiple files.

    Args:
        project_path: Root directory of the Python project
        module_path: Path to module file (relative to project_path), e.g. "app/views/foo.py"

    Returns:
        JSON with success status and new path
    """
    import os
    import shutil

    try:
        # Parse module path
        if not module_path.endswith('.py'):
            raise ValueError(f"module_path must be a .py file, got: {module_path}")

        module_dir = os.path.dirname(module_path)
        module_name = os.path.basename(module_path)[:-3]  # Remove .py

        # Full paths
        full_module_path = os.path.join(project_path, module_path)
        pkg_dir = os.path.join(project_path, module_dir, module_name) if module_dir else os.path.join(project_path, module_name)
        init_path = os.path.join(pkg_dir, "__init__.py")

        # Check source exists
        if not os.path.exists(full_module_path):
            raise ValueError(f"Module '{module_path}' does not exist")

        # Check target dir doesn't exist
        if os.path.exists(pkg_dir):
            raise ValueError(
                f"Directory '{module_name}' already exists. "
                "Remove it first or use a clean state."
            )

        # Create package directory
        os.makedirs(pkg_dir)

        # Move module to __init__.py
        shutil.move(full_module_path, init_path)

        # Calculate relative paths for output
        rel_pkg_dir = os.path.join(module_dir, module_name) if module_dir else module_name
        rel_init_path = os.path.join(rel_pkg_dir, "__init__.py")

        return json.dumps(
            {
                "success": True,
                "new_path": rel_init_path,
                "package_dir": rel_pkg_dir,
                "message": f"Moved {module_path} to {rel_init_path}. No import changes needed!",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def convert_module_to_package(
    project_path: str,
    module_path: str,
) -> str:
    """Convert a module file into a package with the same name.

    Transforms `foo.py` into `foo/foo.py` while updating all imports project-wide.

    Example:
        `views/service_contractor.py` becomes `views/service_contractor/service_contractor.py`
        All imports like `from views.service_contractor import X`
        become `from views.service_contractor.service_contractor import X`

    This is a two-step process using Rope:
    1. Move module to a temporary package (different name to trigger import updates)
    2. Rename the temporary package to the original module name

    Args:
        project_path: Root directory of the Python project
        module_path: Path to module file (relative to project_path), e.g. "app/views/foo.py"

    Returns:
        JSON with success status and list of changed files
    """
    import os

    try:
        project = get_project(project_path)

        # Parse module path
        if not module_path.endswith('.py'):
            raise ValueError(f"module_path must be a .py file, got: {module_path}")

        module_dir = os.path.dirname(module_path)
        module_name = os.path.basename(module_path)[:-3]  # Remove .py

        # Temporary package name (must be different to trigger import updates)
        temp_pkg_name = f"{module_name}__rope_tmp_pkg__"
        temp_pkg_path = os.path.join(module_dir, temp_pkg_name) if module_dir else temp_pkg_name

        # Final package path
        final_pkg_path = os.path.join(module_dir, module_name) if module_dir else module_name

        # Check if target directory already exists
        full_final_path = os.path.join(project_path, final_pkg_path)
        if os.path.exists(full_final_path):
            raise ValueError(
                f"Directory '{final_pkg_path}' already exists. "
                "Remove it first or use a clean state."
            )

        # Step 1: Create temporary package
        project.root.create_folder(temp_pkg_path)
        temp_pkg_resource = project.get_resource(temp_pkg_path)
        temp_pkg_resource.create_file('__init__.py')

        # Step 2: Move module to temporary package
        module_resource = get_resource(project, module_path)
        mover = MoveModule(project, module_resource)
        move_changes = mover.get_changes(temp_pkg_resource)
        project.do(move_changes)

        all_changed_files = set(get_changed_files(move_changes))

        # Step 3: Rename temporary package to final name
        temp_pkg_resource = project.get_resource(temp_pkg_path)
        renamer = Rename(project, temp_pkg_resource, None)
        rename_changes = renamer.get_changes(module_name)
        project.do(rename_changes)

        all_changed_files.update(get_changed_files(rename_changes))

        # Update paths in changed_files to reflect final state
        final_changed_files = []
        for f in all_changed_files:
            # Replace temp package name with final name
            f = f.replace(temp_pkg_name, module_name)
            # Remove the old module.py if it's in the list (it was moved)
            if f != module_path:
                final_changed_files.append(f)

        # Add the final module location
        final_module_path = os.path.join(final_pkg_path, f"{module_name}.py")
        if final_module_path not in final_changed_files:
            final_changed_files.append(final_module_path)

        # Search for string references that may need manual fixing
        # (e.g., mock.patch, lazy imports, etc.)
        import subprocess

        old_import_path = f"{module_dir.replace('/', '.')}.{module_name}".lstrip('.')
        grep_result = subprocess.run(
            ["grep", "-r", "-n", f'"{old_import_path}', project_path,
             "--include=*.py"],
            capture_output=True, text=True
        )
        potential_string_refs = []
        if grep_result.stdout.strip():
            for line in grep_result.stdout.strip().split('\n'):
                # Make paths relative to project
                if line.startswith(project_path):
                    line = line[len(project_path):].lstrip('/')
                potential_string_refs.append(line)

        result = {
            "success": True,
            "changed_files": sorted(final_changed_files),
            "new_module_path": final_module_path,
        }

        if potential_string_refs:
            result["warning_string_references"] = potential_string_refs

        return json.dumps(result, indent=2)
    except RefactoringError as e:
        return json.dumps({"success": False, "error": f"Refactoring error: {e}"})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Unexpected error: {e}"})


def close_rope_project(project_path: str) -> str:
    """Close a Rope project and release resources.

    Call this when done with refactoring to free memory.

    Args:
        project_path: Root directory of the Python project

    Returns:
        JSON with success status
    """
    try:
        close_project(project_path)
        return json.dumps({"success": True, "message": "Project closed"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
