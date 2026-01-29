from pathlib import Path

import libcst as cst

from docgen.generator import FunctionAndClassVisitor


def process_module(file_path: Path, docstring_type: bool) -> bool:
    """
    Function to write docstrings for classes and methods.
    """
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        source_code = file_path.read_text(encoding="utf-8")

        try:
            module = cst.parse_module(source_code)
        except Exception as parse_err:
            print(f"Skipping {file_path} (parse error): {parse_err}")
            return False

        visitor = FunctionAndClassVisitor(
            file_path=file_path, docstring_type=docstring_type
        )
        modified_module = module.visit(visitor)

        # check if the code has been modified
        if modified_module.code != source_code:
            file_path.write_text(modified_module.code, encoding="utf-8")
            print(f"Updated {file_path}")
        else:
            print(f"No changes in {file_path}")

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def check_module(file_path: Path) -> bool:
    """
    Function to check whether the code in `file_path` has docstrings.
    """
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            module = FunctionAndClassVisitor()._store_missing_docstrings(
                file_path
            )
            if module and module.missing_docstrings:
                print(f"Missing docstrings in {module.file_path}:")
                for kind, name in module.missing_docstrings:
                    print(f"  {kind} '{name}'")

        except Exception as parse_err:
            print(f"Skipping {file_path} (parse error): {parse_err}")
            return False

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
