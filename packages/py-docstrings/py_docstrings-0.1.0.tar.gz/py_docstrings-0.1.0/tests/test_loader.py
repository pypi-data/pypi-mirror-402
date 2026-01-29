import tempfile
from pathlib import Path

import pytest

from docgen.generator import get_python_files


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmpdir:
        root = Path(tmpdir)

        # File structure:
        # tmpdir/
        #   a.py
        #   b.txt
        #   .gitignore
        #   subdir/
        #       c.py
        #       d.py

        (root / "a.py").write_text(" ")
        (root / "b.txt").write_text("text file")
        (root / ".gitignore").write_text("subdir/d.py\n")

        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "c.py").write_text(" ")
        (subdir / "d.py").write_text(" ")

        yield root


def test_non_recursive_collect(temp_project):
    files = get_python_files(
        paths=[str(temp_project)], recursive=False, root=temp_project
    )
    file_names = sorted(f.name for f in files)
    assert file_names == ["a.py"]


def test_recursive_collect(temp_project):
    files = get_python_files(
        paths=[str(temp_project)], recursive=True, root=temp_project
    )
    file_names = sorted(f.name for f in files)
    assert file_names == ["a.py", "c.py"]  # d.py is excluded via .gitignore


def test_file_input_absolute(temp_project):
    a_py = temp_project / "a.py"
    files = get_python_files(paths=[str(a_py.resolve())], root=temp_project)
    assert len(files) == 1
    assert files[0].name == "a.py"


def test_file_input_relative():
    rel_path = Path("a.py")
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "a.py").write_text(" ")
        files = get_python_files(paths=[str(root / rel_path)], root=root)
        assert files[0].name == "a.py"
