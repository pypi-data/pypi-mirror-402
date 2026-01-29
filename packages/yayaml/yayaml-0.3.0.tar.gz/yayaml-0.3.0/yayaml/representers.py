"""This module implements custom YAML representer functions"""

from typing import Any, Callable, Union

from .yaml import (
    BaseRepresenter,
    Node,
    RepresenterFunc,
    add_representer,
    is_representer,
)

# -- Multi-purpose representers -----------------------------------------------


def represent_by_type(
    representer: BaseRepresenter,
    obj: Union[list, tuple, dict, Any],
    *,
    tag: str,
) -> Node:
    """A representer for simple types: sequence-like, mapping-like or scalar"""
    if isinstance(obj, (list, tuple)):
        return representer.represent_sequence(tag, list(obj))

    elif isinstance(obj, dict):
        return representer.represent_mapping(tag, obj)

    return representer.represent_scalar(tag, str(obj))


# -- Representer factories ----------------------------------------------------


def build_representer(
    simplify_type: Callable[[Any], Union[list, tuple, dict, Any]]
) -> RepresenterFunc:
    """Builds a representer function from a type simplification callable.

    This factory function creates a representer that first converts the object
    to a simpler type (list, tuple, dict, or scalar) using the provided
    ``simplify_type`` function, then represents it appropriately.

    Args:
        simplify_type: A callable that takes the object to represent and
            returns a simplified version. Return a list/tuple for sequence
            representation, a dict for mapping representation, or any other
            value for scalar representation.

    Returns:
        A representer function suitable for use with ``add_representer``.

    Example:
        >>> from yayaml import add_representer, build_representer
        >>> class Point:
        ...     def __init__(self, x, y):
        ...         self.x, self.y = x, y
        >>> add_representer(
        ...     Point,
        ...     build_representer(lambda pt: [pt.x, pt.y])
        ... )
    """

    def representer_func(representer: BaseRepresenter, obj: Any, *, tag: str):
        return represent_by_type(
            representer,
            simplify_type(obj),
            tag=tag,
        )

    return representer_func


# -- Registration of representers ---------------------------------------------

add_representer(
    slice,
    build_representer(lambda o: [o.start, o.stop, o.step]),
)

add_representer(
    range,
    build_representer(lambda o: [o.start, o.stop, o.step]),
)
