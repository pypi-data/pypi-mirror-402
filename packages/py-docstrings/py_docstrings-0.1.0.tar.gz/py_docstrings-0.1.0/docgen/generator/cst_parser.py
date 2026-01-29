import pathlib
from typing import List, Optional, Tuple

import libcst as cst

from docgen.templates import (
    DOCSTRING_FOR_CLASS,
    DOCSTRING_FOR_FUNCTION,
    DOCSTRING_FOR_CLASS_DEFAULT,
    DOCSTRING_FOR_FUNCTION_DEFAULT,
)


class FunctionAndClassVisitor(cst.CSTTransformer):
    """
    Class for parsing and modifying code inside a module.

    The code is parsed using the parser from libcst. CST in this context is a
    Concrete Syntax Tree. While parsing, we keep track of the indentation
    level, which is used to correctly place the docstring inside the class
    or method.
    The visitor does not modify any function inside another function. Only
    outer level functions and classes (along with their methods) are modified.

    Arguments
    ---------
    file_path: pathlib.Path
        Path location of module.

    """

    def __init__(
        self,
        file_path: pathlib.Path = pathlib.Path.cwd(),
        docstring_type: bool = False,
    ):
        self.stack: List[Tuple[str, ...]] = []
        self.missing_docstrings = []
        self.indent_level = 0  # track no. of whitespaces at current level
        self.file_path = file_path
        if docstring_type is False:
            self.class_docstring = DOCSTRING_FOR_CLASS_DEFAULT
            self.function_docstring = DOCSTRING_FOR_FUNCTION_DEFAULT
        else:
            self.class_docstring = DOCSTRING_FOR_CLASS
            self.function_docstring = DOCSTRING_FOR_FUNCTION

    def _build_indented_docstring(self, raw_text: str, indent_ws: str) -> str:
        lines = raw_text.strip("\n").splitlines()
        formatted_lines = ['"""' + lines[0]]
        num_whitespaces = indent_ws

        for line in lines[1:]:

            if not line.strip():        # skip unnecessary indentation for empty lines
                formatted_lines.append(line)
            else:
                formatted_lines.append(num_whitespaces + line)

        formatted_lines.append(num_whitespaces + '"""')
        return "\n".join(formatted_lines)

    def _get_indent_level(self, node: cst.CSTNode) -> int:

        if node.body.indent is not None:
            indent_ws = len(node.body.indent)

        elif node.body.body:
            first_stmt = node.body.body[0]
            # If not string -> standard indent of 4 whitespaces
            indent_ws = (
                len(first_stmt.leading_lines[0].indent.value)
                if first_stmt.leading_lines
                and isinstance(first_stmt.leading_lines[0].indent, str)
                else 4
            )
        else:
            indent_ws = 4

        return indent_ws

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:

        self.indent_level += self._get_indent_level(node)
        self.stack.append(node)
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:

        indent_ws = self.indent_level * " "
        current_indent = self._get_indent_level(original_node)
        self.indent_level -= current_indent

        if original_node.get_docstring() is not None:
            return updated_node

        self.missing_docstrings.append(("class", original_node.name.value))

        # Determine indentation based on the body
        final_docstring = self._build_indented_docstring(
            self.class_docstring, indent_ws
        )

        docstring_stmt = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(final_docstring))],
        )
        new_body = updated_node.body.with_changes(
            body=[docstring_stmt] + list(updated_node.body.body)
        )

        return updated_node.with_changes(body=new_body)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.indent_level += self._get_indent_level(node)
        self.stack.append(node)

        # Do not visit functions inside functions
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:

        indent_ws = self.indent_level * " "
        current_indent = self._get_indent_level(original_node)
        self.indent_level -= current_indent

        if original_node.get_docstring() is not None:
            return updated_node

        self.missing_docstrings.append(("function", original_node.name.value))

        # Determine indentation based on the body
        final_docstring = self._build_indented_docstring(
            self.function_docstring, indent_ws
        )

        docstring_stmt = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(final_docstring))],
        )
        new_body = updated_node.body.with_changes(
            body=[docstring_stmt] + list(updated_node.body.body)
        )

        return updated_node.with_changes(body=new_body)

    @classmethod
    def _store_missing_docstrings(cls, file_path: pathlib.Path) -> cst.Module:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        module = cst.parse_module(source_code)

        visitor = cls(file_path=file_path)
        module.visit(visitor)

        return visitor
