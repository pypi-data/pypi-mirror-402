"""
:py:mod:`yayaml`: A package providing tools for working with YAML.

Specifically, it makes it simpler to add custom constructors or representers,
and adds a whole suite of constructors for basic Python functions.
"""

# Public interface
from .constructors import construct_from_func, scalar_node_to_object
from .exceptions import (
    ConstructorError,
    RepresenterError,
    add_yaml_error_hint,
    raise_improved_exception,
)
from .io import load_yml, write_yml, yaml_dumps, yaml_dumps_plain
from .representers import build_representer
from .yaml import (
    add_constructor,
    add_representer,
    is_constructor,
    is_representer,
    yaml,
    yaml_safe,
)

__version__ = "0.3.0"
