from pathlib import Path
from typing import List, Optional

import pathspec

# file paths are expected as - no argument (all python files
# in current directory) or specific file paths


def load_gitignore(root: Path) -> pathspec.PathSpec:
    """
    Load patterns from .gitignore in the root directory.
    If no .gitignore exists, return an empty spec.
    """
    gitignore_file = root / ".gitignore"
    if gitignore_file.exists():
        patterns = gitignore_file.read_text().splitlines()
        return pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern, patterns
        )
    return pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern, []
    )


def get_root_dir(file_paths: Optional[List[str]] = None) -> Path:
    """Return the root directory from where to start collecting files."""
    if not file_paths:
        return Path.cwd()
    return Path(file_paths[0]).parent if len(file_paths) == 1 else Path.cwd()


def is_python_file(path: Path) -> bool:
    """Check if the path is a Python file."""
    return path.is_file() and path.suffix == ".py"


def is_git_ignored(
    path: Path, root: Path, gitignore_pattern: pathspec.PathSpec
) -> bool:
    # empty gitignore
    if gitignore_pattern.patterns == []:
        return False

    try:
        rel_path = path.relative_to(root)
    except ValueError:
        rel_path = path
    return gitignore_pattern.match_file(str(rel_path))


def get_python_files(
    paths: Optional[List[str]] = None,
    recursive: bool = False,
    root: Optional[Path] = None,
) -> List[Path]:
    """
    Given a list of files or directory paths, return all valid Python files.
    If no path is given, use the current directory.
    """
    root = root or Path.cwd()
    paths = paths or ["."]
    all_files = []
    spec = load_gitignore(root)

    for p in paths:
        path = Path(p)
        if is_python_file(path):
            all_files.append(path)
        elif path.is_dir():
            iterator = path.rglob("*.py") if recursive else path.glob("*.py")
            all_files.extend(
                f
                for f in iterator
                if f.is_file() and not is_git_ignored(f, root, spec)
            )

    return all_files
