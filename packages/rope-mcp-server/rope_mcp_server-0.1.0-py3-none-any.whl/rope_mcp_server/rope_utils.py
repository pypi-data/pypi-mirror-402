"""Rope utility functions for project caching and change handling."""

from pathlib import Path
from typing import Dict, List

from rope.base.prefs import ImportPrefs
from rope.base.project import Project
from rope.base.resources import Resource

_project_cache: Dict[str, Project] = {}


def get_project(path: str, ropefolder: str | None = ".ropeproject") -> Project:
    """Get or create a cached Rope Project instance.

    Args:
        path: Root directory of the Python project
        ropefolder: Name of rope folder, or None to disable persistence

    Returns:
        Rope Project instance
    """
    resolved_path = str(Path(path).resolve())
    if resolved_path not in _project_cache:
        project = Project(resolved_path, ropefolder=ropefolder)
        # Use 'from module import symbol' style instead of 'import module'
        project.prefs.imports = ImportPrefs(preferred_import_style="from-global")
        _project_cache[resolved_path] = project
    return _project_cache[resolved_path]


def close_project(path: str) -> None:
    """Close and remove a project from the cache.

    Args:
        path: Root directory of the Python project
    """
    resolved_path = str(Path(path).resolve())
    if resolved_path in _project_cache:
        try:
            _project_cache[resolved_path].close()
        except FileNotFoundError:
            # .ropeproject folder may have been deleted already, that's fine
            pass
        del _project_cache[resolved_path]


def close_all_projects() -> None:
    """Close all cached projects."""
    for project in _project_cache.values():
        try:
            project.close()
        except FileNotFoundError:
            # .ropeproject folder may have been deleted already, that's fine
            pass
    _project_cache.clear()


def get_changed_files(changes) -> List[str]:
    """Extract list of changed file paths from Rope ChangeSet.

    Args:
        changes: Rope ChangeSet object

    Returns:
        List of relative file paths that were changed
    """
    changed_files = []
    for change in changes.get_changed_resources():
        if isinstance(change, Resource):
            changed_files.append(change.path)
    return changed_files


def get_resource(project: Project, file_path: str) -> Resource:
    """Get a Rope Resource for a file path.

    Args:
        project: Rope Project instance
        file_path: Path relative to project root

    Returns:
        Rope Resource object
    """
    return project.get_resource(file_path)


def create_file_if_not_exists(project: Project, file_path: str) -> Resource:
    """Create a file if it doesn't exist and return its Resource.

    Args:
        project: Rope Project instance
        file_path: Path relative to project root

    Returns:
        Rope Resource object
    """
    try:
        return project.get_resource(file_path)
    except Exception:
        # Create the file
        project.root.create_file(file_path)
        return project.get_resource(file_path)
