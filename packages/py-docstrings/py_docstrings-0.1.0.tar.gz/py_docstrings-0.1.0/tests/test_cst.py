import re
import libcst as cst

from pathlib import Path
from docgen.generator import (
    FunctionAndClassVisitor,
)


def test_function_docstring():
    function_str = Path("tests/testfiles/input_1.py").read_text(
        encoding="utf-8"
    )

    module = cst.parse_module(function_str)
    visitor = FunctionAndClassVisitor(file_path=None)
    modified_module = module.visit(visitor)

    result_loc = Path("tests/testfiles/expected_1.py")
    result_code = result_loc.read_text(encoding="utf-8")

    lines_modified = modified_module.code.split("\n")
    lines_result = result_code.split("\n")

    # either lines consist of whitespaces, or they match exactly
    for i in range(len(lines_modified)):
        assert (
            re.match(r"\s+", lines_modified[i])
            or re.match(r"\s+", lines_result[i])
            or lines_modified[i] == lines_result[i]
        )


def test_class_docstring():
    class_str = Path("tests/testfiles/input_2.py").read_text(encoding="utf-8")

    module = cst.parse_module(class_str)
    visitor = FunctionAndClassVisitor(file_path=None)
    modified_module = module.visit(visitor)

    result_loc = Path("tests/testfiles/expected_2.py")
    result_code = result_loc.read_text(encoding="utf-8")

    lines_modified = modified_module.code.split("\n")
    lines_result = result_code.split("\n")

    for i in range(len(lines_modified)):
        assert (
            re.match(r"\s+", lines_modified[i])
            or re.match(r"\s+", lines_result[i])
            or lines_modified[i] == lines_result[i]
        )


def test_mixed_docstring():
    mixed_str = Path("tests/testfiles/input_3.py").read_text(encoding="utf-8")

    module = cst.parse_module(mixed_str)
    visitor = FunctionAndClassVisitor(file_path=None)
    modified_module = module.visit(visitor)

    result_loc = Path("tests/testfiles/expected_3.py")
    result_code = result_loc.read_text(encoding="utf-8")

    lines_modified = modified_module.code.split("\n")
    lines_result = result_code.split("\n")

    for i in range(len(lines_modified)):
        assert (
            re.match(r"\s+", lines_modified[i])
            or re.match(r"\s+", lines_result[i])
            or lines_modified[i] == lines_result[i]
        )
