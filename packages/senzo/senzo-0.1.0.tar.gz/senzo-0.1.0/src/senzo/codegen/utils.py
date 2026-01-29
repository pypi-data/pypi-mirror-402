"""LibCST utilities for code generation."""

from __future__ import annotations

from typing import Sequence

import libcst as cst


def make_name(name: str) -> cst.Name:
    """Create a Name node."""
    return cst.Name(name)


def make_annotation(type_str: str) -> cst.Annotation:
    """Create an Annotation node from a type string."""
    return cst.Annotation(annotation=cst.parse_expression(type_str))


def make_simple_string(value: str) -> cst.SimpleString:
    """Create a SimpleString node."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return cst.SimpleString(f'"{escaped}"')


def make_docstring(text: str) -> cst.SimpleStatementLine:
    """Create a docstring statement."""
    escaped = text.replace('"""', r"\"\"\"")
    return cst.SimpleStatementLine(
        body=[cst.Expr(value=cst.SimpleString(f'"""{escaped}"""'))]
    )


def make_assign(
    target: str,
    value: cst.BaseExpression,
    annotation: str | None = None,
) -> cst.SimpleStatementLine:
    """Create an assignment statement."""
    if annotation:
        return cst.SimpleStatementLine(
            body=[
                cst.AnnAssign(
                    target=cst.Name(target),
                    annotation=make_annotation(annotation),
                    value=value,
                )
            ]
        )
    return cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(target))],
                value=value,
            )
        ]
    )


def make_import_from(
    module: str,
    names: Sequence[str],
) -> cst.SimpleStatementLine:
    """Create an import from statement."""
    import_names = [cst.ImportAlias(name=cst.Name(n)) for n in names]
    return cst.SimpleStatementLine(
        body=[
            cst.ImportFrom(
                module=cst.Attribute(
                    value=cst.parse_expression(module.rsplit(".", 1)[0]),
                    attr=cst.Name(module.rsplit(".", 1)[1]),
                )
                if "." in module
                else cst.Name(module),
                names=import_names,
            )
        ]
    )


def make_module(
    body: Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
) -> cst.Module:
    """Create a Module node."""
    return cst.Module(body=list(body))


def make_class_def(
    name: str,
    bases: Sequence[str],
    body: Sequence[cst.BaseStatement],
    decorators: Sequence[cst.Decorator] | None = None,
) -> cst.ClassDef:
    """Create a ClassDef node."""
    base_args = [cst.Arg(value=cst.parse_expression(b)) for b in bases]
    return cst.ClassDef(
        name=cst.Name(name),
        bases=base_args,
        body=cst.IndentedBlock(body=list(body)),
        decorators=list(decorators) if decorators else [],
    )


def make_function_def(
    name: str,
    params: Sequence[cst.Param],
    body: Sequence[cst.BaseStatement],
    returns: str | None = None,
    decorators: Sequence[cst.Decorator] | None = None,
    is_async: bool = False,
) -> cst.FunctionDef:
    """Create a FunctionDef node."""
    return_annotation = make_annotation(returns) if returns else None
    func = cst.FunctionDef(
        name=cst.Name(name),
        params=cst.Parameters(params=list(params)),
        body=cst.IndentedBlock(body=list(body)),
        returns=return_annotation,
        decorators=list(decorators) if decorators else [],
        asynchronous=cst.Asynchronous() if is_async else None,
    )
    return func


def make_param(
    name: str,
    annotation: str | None = None,
    default: cst.BaseExpression | None = None,
) -> cst.Param:
    """Create a function parameter."""
    return cst.Param(
        name=cst.Name(name),
        annotation=make_annotation(annotation) if annotation else None,
        default=default,
    )
