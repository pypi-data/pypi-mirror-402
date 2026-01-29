"""Various tools"""

import re
from typing import List, Union

import numpy as np

# -----------------------------------------------------------------------------


def str2bool(val: str) -> bool:
    """Copy of strtobool from deprecated distutils package"""
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"Invalid truth value {repr(val)}!")


def collapse_whitespace(s: str) -> str:
    """Replaces runs (two or more) of whitespace (space, tab, line break) with
    a single space and strips leading or trailing whitespace."""
    return re.sub(r"\s+", " ", s).strip()


def eval_simple_math_expr(s: str) -> Union[int, float]:
    """Evalautes simple mathematical expressions, given by strings.

    Supports: +, -, *, **, /, e-X, eX, inf, nan
    """
    # Remove spaces
    expr_str = s.replace(" ", "")

    # Parse some special strings
    if expr_str in ("nan", "NaN"):
        return float("nan")

    # NOTE these will cause errors if emitted file is not read by python!
    elif expr_str in ("np.inf", "inf", "INF"):
        return np.inf

    elif expr_str in ("-np.inf", "-inf", "-INF"):
        return -np.inf

    # remove everything that might cause trouble -- only allow digits, dot, +,
    # -, *, /, and eE to allow for writing exponentials, and parentheses
    expr_str = re.sub(r"[^0-9eE\-.+\*\/\(\)]", "", expr_str)

    # Try to eval
    return eval(expr_str)


def listgen(
    *,
    from_range: list = None,
    unique: bool = False,
    sort: bool = True,
    append: list = None,
    remove: list = None,
) -> List[int]:
    """Generates a list of integer elements.

    Args:
        from_range (list, optional): range arguments to use as the basis of the
            list
        unique (bool, optional): Whether to ascertain uniqueness of elements
        sort (bool, optional): Whether to sort the list before returning
        append (list, optional): Additional elements to append to the list
        remove (list, optional): Elements to remove all occurrences of

    Returns:
        List[int]: The generated list
    """
    l = []
    if from_range:
        l += list(range(*from_range))

    if append:
        l += append

    if remove:
        for element_to_remove in list(set(remove)):
            while element_to_remove in l:
                l.remove(element_to_remove)

    if unique:
        l = list(set(l))

    if sort:
        l.sort()

    return l
