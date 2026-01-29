"""Defines and registers YAML constructors."""

import copy as _copy
import operator as _operator
import os
import platform
import sys
from functools import partial as _partial
from functools import reduce as _reduce
from typing import Any, Callable

import numpy as np
import ruamel.yaml

from . import tools
from .yaml import (
    BaseLoader,
    ConstructorFunc,
    Node,
    add_constructor,
    is_constructor,
)

# -- Multi-purpose constructors -----------------------------------------------
# ... can be specialized by applying `functools.partial`


def scalar_node_to_object(loader: BaseLoader, node: Node):
    """Attempts to convert the given scalar node to a null (Python None),
    a bool, an int, or a float object using the corresponding YAML constructor.
    If those conversions fail, constructs a scalar (which will typically result
    in a string being returned).
    """

    def construct_yaml_null(node) -> None:
        """Constructs a None from an appropriate YAML node.

        This custom constructor should not be necessary, but for some weird
        reason, the ruamel.yaml constructor from loader.construct_yaml_null
        *always* returns None, regardless of the value of the node. As we rely
        on errors being raised if construction fails, we need this custom
        constructor for the two explicitly allowed null values.
        """
        if node.value in ("~", "null"):
            return None
        raise ruamel.yaml.constructor.ConstructorError(
            f"expected null, but " f"got '{node.value}'"
        )

    for constructor in (
        loader.construct_yaml_bool,
        loader.construct_yaml_int,
        loader.construct_yaml_float,
        construct_yaml_null,
        loader.construct_yaml_str,
    ):
        try:
            return constructor(node)
        except Exception:
            pass

    # Fallback -- very difficult to reach
    return loader.construct_scalar(node)


def construct_from_func(
    loader: BaseLoader, node: Node, *, func: Callable, unpack: bool = True
) -> Any:
    """A constructor that constructs a scalar, mapping, or sequence from the
    given node and subsequently applies the given function on it.

    Args:
        loader: The selected YAML loader
        node: The node from which to construct a Python object
        func (Callable): The callable to invoke on the resulting
        unpack (bool, optional): Whether to unpack sequences or mappings into
            the ``func`` call
    """

    def invoke_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            raise ruamel.yaml.constructor.ConstructorError(
                "Constructing Python object from a tagged YAML node failed: "
                f"Got a {type(exc).__name__}: {exc}\n\n"
                f"Constructor:           {func}\n"
                f"Positional arguments:  {args}\n"
                f"Keyword arguments:     {kwargs}\n\n"
                "Check that the syntax was correct and the arguments have the "
                "expected types."
            ) from exc

    if isinstance(node, ruamel.yaml.nodes.MappingNode):
        s = loader.construct_mapping(node, deep=True)
        if unpack:
            return invoke_func(**s)

    elif isinstance(node, ruamel.yaml.nodes.SequenceNode):
        s = loader.construct_sequence(node, deep=True)
        if unpack:
            return invoke_func(*s)

    else:
        s = scalar_node_to_object(loader, node)

    return invoke_func(s)


# -- Batch-registration of simple constructors --------------------------------

# Programmatically define and add constructors, which
# evaluate nodes directly during construction. Distinguish between those where
# sequence or mapping arguments are NOT to be unpacked and those where
# unpacking them as positional and/or keyword arguments makes sense.
_func_constructors_no_unpack = [
    # built-ins operating on iterables
    ("!any", any),
    ("!all", all),
    ("!min", min),
    ("!max", max),
    ("!sum", sum),
    ("!prod", lambda a: _reduce(_operator.mul, a, 1)),
    ("!sorted", lambda a: list(sorted(a))),
    ("!isorted", lambda a: list(sorted(a, reverse=True))),
    #
    # built-ins operating on scalars
    ("!abs", lambda v: abs(float(v))),
    ("!int", lambda v: int(float(v))),
    ("!round", lambda v: round(float(v))),
    #
    # working with paths
    ("!expanduser", os.path.expanduser),
    #
    # numpy
    ("!array", np.array),
    #
    # misc
    ("!str-to-bool", tools.str2bool),
    ("!deepcopy", _copy.deepcopy),
    ("!collapse-whitespace", tools.collapse_whitespace),
    ("!oneline", tools.collapse_whitespace),
]

_func_constructors_unpack = [
    # simple python types
    ("!slice", slice),
    ("!range", range),
    #
    # from operators module
    ("!add", _operator.add),
    ("!sub", _operator.sub),
    ("!mul", _operator.mul),
    ("!truediv", _operator.truediv),
    ("!floordiv", _operator.floordiv),
    ("!mod", _operator.mod),
    ("!pow", lambda x, y, z=None: pow(x, y, z)),
    ("!not", _operator.not_),
    ("!and", _operator.and_),
    ("!or", _operator.or_),
    ("!xor", _operator.xor),
    ("!lt", _operator.lt),
    ("!le", _operator.le),
    ("!eq", _operator.eq),
    ("!ne", _operator.ne),
    ("!neq", _operator.ne),
    ("!ge", _operator.ge),
    ("!gt", _operator.gt),
    ("!negate", _operator.neg),
    ("!invert", _operator.invert),
    ("!contains", _operator.contains),
    ("!concat", lambda *a: _reduce(_operator.concat, a, [])),
    ("!format", lambda fstr, *a, **k: fstr.format(*a, **k)),
    ("!join", lambda jstr, elements: jstr.join(elements)),
    ("!split", lambda s, *a: s.split(*a)),
    #
    # conditionals
    ("!if-else", lambda cond, a, b: a if cond else b),
    (
        "!if-unix-else",
        lambda a, b: a if platform.system() in ("Linux", "Darwin") else b,
    ),
    (
        "!if-windows-else",
        lambda a, b: a if platform.system() == "Windows" else b,
    ),
    #
    # numpy
    ("!arange", lambda *a: [float(f) for f in np.arange(*a)]),
    ("!linspace", lambda *a: [float(f) for f in np.linspace(*a)]),
    ("!logspace", lambda *a: [float(f) for f in np.logspace(*a)]),
    #
    # working with paths
    ("!joinpath", os.path.join),
]


# Add all of the above as constructors by specializing the func-constructor
for tag, func in _func_constructors_unpack:
    add_constructor(tag, _partial(construct_from_func, func=func, unpack=True))

for tag, func in _func_constructors_no_unpack:
    add_constructor(
        tag, _partial(construct_from_func, func=func, unpack=False)
    )


# -- Specialized constructors -------------------------------------------------


@is_constructor("!getenv", aliases=("!env",))
def getenv(loader: BaseLoader, node: Node):
    """Retrieves an environment variable by name, optionally with fallback"""
    if isinstance(node, ruamel.yaml.nodes.SequenceNode):
        return os.environ.get(*loader.construct_sequence(node, deep=True))
    return os.environ[str(loader.construct_scalar(node))]


@is_constructor("!len")
def get_length(loader: BaseLoader, node: Node):
    """Returns the length of a sequence or mapping"""
    wrapper_seq = loader.construct_sequence(node, deep=True)
    return len(wrapper_seq[0])


@is_constructor("!getboolenv", aliases=("!boolenv",))
def getboolenv(loader: BaseLoader, node: Node) -> bool:
    """Retrieves an environment variable by name, optionally with fallback,
    and evaluates it as a boolean."""
    envvar = getenv(loader, node)
    if isinstance(envvar, str):
        return tools.str2bool(envvar)
    return envvar


@is_constructor(
    "!expr",
    aliases=("!expression", "!compute"),
    hint="Check the expression syntax",
)
def expression(loader: BaseLoader, node: Node):
    """Constructor that evaluates strings of simple mathematical expressions"""
    expr_str = loader.construct_scalar(node)
    return tools.eval_simple_math_expr(expr_str)


@is_constructor("!listgen")
def listgen(loader: BaseLoader, node: Node):
    """Constructor for lists, where node can be a mapping or sequence"""
    if isinstance(node, ruamel.yaml.nodes.MappingNode):
        kwargs = loader.construct_mapping(node, deep=True)

    elif isinstance(node, ruamel.yaml.nodes.SequenceNode):
        kwargs = dict(from_range=loader.construct_sequence(node))

    else:
        raise TypeError(
            f"Expected mapping or sequence node for !listgen, but "
            f"got {type(node)}!"
        )

    return tools.listgen(**kwargs)
