from typing import Any

from evalis.antlr4_adapter import parse_expression_tree
from evalis.ast import AstBuilder, EvalisNode
from evalis.error import syntax_error
from evalis.eval import Evaluator
from evalis.types import (
    EvaluatorOptions,
    ParseResult,
    ParseResultError,
    ParseResultSuccess,
)


def parse_ast(expression: str) -> ParseResult:
    """Parse expression and return ParseResult with ast or errors.

    Does NOT throw - returns a result object that contains either:
    - ast: The parsed AST node
    - errors: Tuple of syntax errors

    For simple use cases, use evaluate_expression() which throws on errors.
    """
    tree, errors = parse_expression_tree(expression)

    if errors:
        return ParseResultError(ast=None, errors=errors)

    builder = AstBuilder()
    ast = builder.visit(tree)
    return ParseResultSuccess(ast=ast, errors=None)


def evaluate_ast(
    node: EvalisNode,
    context: dict[str, Any] = {},
    options: EvaluatorOptions = EvaluatorOptions(),
) -> Any:
    evaluator = Evaluator(options)
    result = evaluator.evaluate(node, context)

    return result


def evaluate_expression(
    expression: str,
    context: dict[str, Any] = {},
    options: EvaluatorOptions = EvaluatorOptions(),
) -> Any:
    """Evaluate expression and return result.

    Throws EvalisError if there are syntax errors.
    For non-throwing parse, use parse_ast() directly.
    """
    result = parse_ast(expression)

    if isinstance(result, ParseResultError):
        raise syntax_error(result.errors)

    return evaluate_ast(result.ast, context, options)
