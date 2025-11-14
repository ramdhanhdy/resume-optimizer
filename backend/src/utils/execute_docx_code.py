"""Execute LLM-generated Python code to create DOCX in a sandboxed manner."""

from __future__ import annotations

import ast
import io
from typing import Any, Dict

import builtins as py_builtins
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from .docx_generator import add_header_row, add_horizontal_line, set_font
from .page_controller import apply_spacing_adjustments, create_section_header, add_bullet_point


class UnsafeCodeError(ValueError):
    """Raised when generated code is deemed unsafe."""


ALLOWED_MODULES = (
    "docx",
    "datetime",
    "time",
    "math",
    "statistics",
    "random",
    "decimal",
    "fractions",
    "collections",
    "itertools",
    "re",
    "textwrap",
)

BANNED_NAMES = {
    "__builtins__",
    "__import__",
    "eval",
    "exec",
    "globals",
    "locals",
    "open",
    "compile",
    "input",
    "vars",
}


def _is_allowed_module(module: str) -> bool:
    base = module.split(".")[0]
    return any(
        module == allowed
        or module.startswith(f"{allowed}.")
        or base == allowed
        for allowed in ALLOWED_MODULES
    )


def _safe_import(
    name: str,
    globals_: Any = None,
    locals_: Any = None,
    fromlist: Any = (),
    level: int = 0,
):
    """Restrict imports to approved modules."""
    # Resolve absolute module name when using relative imports (disallow level > 0)
    if level != 0:
        raise UnsafeCodeError("Relative imports are not allowed.")

    full_name = name
    if not _is_allowed_module(full_name):
        raise UnsafeCodeError(f"Import of module '{full_name}' is not allowed.")

    return py_builtins.__import__(full_name, globals_, locals_, fromlist, level)


SAFE_BUILTINS: Dict[str, Any] = {
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "min": min,
    "max": max,
    "sum": sum,
    "zip": zip,
    "sorted": sorted,
    "round": round,
    "all": all,
    "any": any,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "__import__": _safe_import,
}


SAFE_GLOBALS: Dict[str, Any] = {
    "__builtins__": SAFE_BUILTINS,
    # Provide commonly used docx symbols so imports are optional
    "Document": Document,
    "Inches": Inches,
    "Pt": Pt,
    "WD_ALIGN_PARAGRAPH": WD_ALIGN_PARAGRAPH,
    "qn": qn,
    "OxmlElement": OxmlElement,
    "set_font": set_font,
    "add_horizontal_line": add_horizontal_line,
    "add_header_row": add_header_row,
    "apply_spacing_adjustments": apply_spacing_adjustments,
    "create_section_header": create_section_header,
    "add_bullet_point": add_bullet_point,
}


def _strip_markdown_wrappers(code: str) -> str:
    """Remove common markdown fences around code blocks."""
    code = code.strip()

    if "```python" in code:
        start = code.find("```python") + len("```python")
        end = code.find("```", start)
        if end != -1:
            code = code[start:end]
    elif code.startswith('"python') or code.startswith("python\n"):
        lines = code.split("\n")
        if lines[0].strip() in ['"python', "python", '"python"']:
            lines = lines[1:]
        code = "\n".join(lines)
    elif "```" in code:
        start = code.find("```") + len("```")
        end = code.find("```", start)
        if end != -1:
            code = code[start:end]

    return code.strip().rstrip('"').rstrip()


def _validate_ast(tree: ast.AST) -> None:
    """Walk the AST and reject unsafe constructs."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None)
            names = [alias.name for alias in getattr(node, "names", [])]
            if module is None and names:
                for alias in names:
                    if not _is_allowed_module(alias):
                        raise UnsafeCodeError(
                            f"Import of module '{alias}' is not allowed."
                        )
            else:
                if module is None:
                    raise UnsafeCodeError("Empty import statements are not allowed.")
                if not _is_allowed_module(module):
                    raise UnsafeCodeError(
                        f"Import of module '{module}' is not allowed."
                    )

        if isinstance(node, ast.Attribute) and node.attr in BANNED_NAMES:
            raise UnsafeCodeError(f"Use of attribute '{node.attr}' is not allowed.")

        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise UnsafeCodeError(f"Use of name '{node.id}' is not allowed.")

        if isinstance(node, (ast.Call, ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in BANNED_NAMES:
                    raise UnsafeCodeError(f"Call to '{func.id}' is not allowed.")
                if isinstance(func, ast.Attribute) and func.attr in BANNED_NAMES:
                    raise UnsafeCodeError(f"Call to '{func.attr}' is not allowed.")
            else:
                if isinstance(node, ast.Assign):
                    targets = node.targets
                elif isinstance(node, ast.AugAssign):
                    targets = [node.target]
                elif isinstance(node, ast.AnnAssign) and node.target is not None:
                    targets = [node.target]

                for target in targets:
                    if isinstance(target, ast.Name) and target.id in BANNED_NAMES:
                        raise UnsafeCodeError(
                            f"Assignment to '{target.id}' is not allowed."
                        )


def execute_docx_code(code: str) -> bytes:
    """
    Execute Python code that generates a DOCX document inside a restricted sandbox.

    Args:
        code: Python code string that creates a DOCX and exposes it via a variable named 'doc'.

    Returns:
        DOCX file as bytes.
    """
    cleaned_code = _strip_markdown_wrappers(code)

    if not cleaned_code:
        raise ValueError("No executable code found.")

    try:
        tree = ast.parse(cleaned_code, mode="exec")
    except SyntaxError as exc:
        # Provide detailed error context
        lines = cleaned_code.split('\n')
        error_line = exc.lineno if exc.lineno else 0
        context_start = max(0, error_line - 3)
        context_end = min(len(lines), error_line + 2)
        
        context = "\n".join([
            f"{'>>> ' if i == error_line - 1 else '    '}{i+1}: {lines[i]}"
            for i in range(context_start, context_end)
        ])
        
        error_msg = (
            f"Generated code could not be parsed: {exc}\n"
            f"Error at line {error_line}: {exc.text if exc.text else '(no text)'}\n"
            f"Context:\n{context}"
        )
        raise ValueError(error_msg) from exc

    _validate_ast(tree)

    sandbox_globals: Dict[str, Any] = dict(SAFE_GLOBALS)
    sandbox_locals: Dict[str, Any] = {}

    try:
        exec(
            compile(tree, filename="<generated-docx>", mode="exec"),
            sandbox_globals,
            sandbox_locals,
        )
    except UnsafeCodeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Error while executing generated code: {exc}") from exc

    namespace: Dict[str, Any] = {**sandbox_globals, **sandbox_locals}

    if "doc" not in namespace:
        raise ValueError("Generated code did not create a 'doc' variable.")

    doc = namespace["doc"]

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.read()
