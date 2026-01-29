"""Custom exceptions and exception handling"""

from typing import Callable, List, Tuple

import ruamel.yaml
from ruamel.yaml.constructor import ConstructorError
from ruamel.yaml.representer import RepresenterError

# -- Custom exception types ---------------------------------------------------
# Aliases for now:

RepresenterError = ruamel.yaml.representer.RepresenterError
ConstructorError = ruamel.yaml.constructor.ConstructorError


# -- Error hints --------------------------------------------------------------


def raise_improved_exception(
    exc: Exception,
    *,
    hints: List[Tuple[Callable[[Exception], bool], str]] = [],
) -> None:
    """Improves the given exception by appending one or multiple hint messages.

    The ``hints`` argument should be a list of 2-tuples, consisting of a unary
    matching function, expecting the exception as only argument, and a hint
    that is part of the new error message.
    """
    matching_hints = []
    for match_func, hint in hints:
        if match_func(exc):
            matching_hints.append(hint)

    if matching_hints:
        _hints = "\n".join(f"  - {h}" for h in matching_hints)
        raise type(exc)(
            str(exc) + f"\n\nHint(s) how to resolve this:\n{_hints}"
        ) from exc

    # Re-raise the active exception
    raise


# .............................................................................

YAML_ERROR_HINTS: List[Tuple[Callable[[Exception], bool], str]] = [
    (
        lambda e: "expected ',' or ']'" in str(e),
        "Did you include a space after the YAML tag defined in that line?",
    ),
    #
    # Default case, always true:
    (
        lambda e: True,
        "Read the error message above for details about the error location.",
    ),
]
"""These are evaluated by :py:func:`.raise_improved_exception`
and from within :py:func:`.load_yml`.

Entries are of the form ``(match function, hint string)`` and can also be
added via :py:func:`.add_yaml_error_hint`.
"""


def add_yaml_error_hint(match_func: Callable[[Exception], bool], hint: str):
    """Adds an error hint for YAML error messages."""
    # Take into account that the last match function will always be true in the
    # case of the YAML error hints
    YAML_ERROR_HINTS.insert(
        max(0, len(YAML_ERROR_HINTS) - 1),
        (match_func, hint),
    )
