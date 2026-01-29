"""This module registers various YAML constructors and representers.

Furthermore, it defines a shared ``ruamel.yaml.YAML`` object that can be
imported and used for loading and storing YAML files using the representers and
constructors.
"""

from functools import partial as partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import ruamel.yaml

from .exceptions import add_yaml_error_hint

# -- Types --------------------------------------------------------------------

Node = ruamel.yaml.nodes.Node

BaseLoader = ruamel.yaml.loader.BaseLoader

BaseRepresenter = ruamel.yaml.representer.BaseRepresenter

# .............................................................................

RepresenterFunc = Callable[[BaseRepresenter, Any, str], Node]

ResolvedRepresenterFunc = Callable[[BaseRepresenter, Any], Node]

ConstructorFunc = Callable[[BaseLoader, Node], Any]


# -- YAML objects -------------------------------------------------------------
yaml_safe: ruamel.yaml.YAML = ruamel.yaml.YAML(typ="safe")
"""An explicitly 'safe' YAML object"""

yaml: ruamel.yaml.YAML = yaml_safe
"""The default YAML object of yayaml"""


# -- Registration of representers and constructors ----------------------------

_REPRESENTERS: Dict[type, ResolvedRepresenterFunc] = {}
"""All representers that have been added by yayaml"""

_CONSTRUCTORS: Dict[str, ConstructorFunc] = {}
"""All constructors that have been added by yayaml"""

# .............................................................................


def add_representer(
    t: type,
    representer: RepresenterFunc,
    *,
    tag: Optional[str] = None,
    _yaml: Optional[ruamel.yaml.YAML] = None,
):
    """Adds a representer function for the given type"""
    if tag is None:
        tag = f"!{t.__name__}"

    resolved_representer = partial(representer, tag=tag)
    _REPRESENTERS[t] = resolved_representer

    if _yaml is None:
        yaml_safe.representer.add_representer(t, resolved_representer)
    else:
        _yaml.representer.add_representer(t, resolved_representer)


def add_constructor(
    tag: str,
    constructor: ConstructorFunc,
    *,
    aliases: List[str] = None,
    hint: Union[str, Tuple[Callable[[Exception], bool], str]] = None,
    _yaml: Optional[ruamel.yaml.YAML] = None,
):
    """Adds a constructor function for the given tag and optional aliases."""
    _CONSTRUCTORS[tag] = constructor

    if _yaml is None:
        yaml_safe.constructor.add_constructor(tag, constructor)
    else:
        _yaml.constructor.add_constructor(tag, constructor)

    # May want to add an error hint for that tag
    if hint:
        if isinstance(hint, str):
            match_func = lambda e: tag in str(e)
        else:
            match_func, hint = hint
        add_yaml_error_hint(match_func, hint)

    # Also register aliases with the same constructor and hint
    if aliases:
        for alias in aliases:
            add_constructor(alias, constructor, hint=hint, _yaml=_yaml)


# .. Decorators ...............................................................


def is_representer(
    t: type,
    *,
    tag: Optional[str] = None,
    _yaml: Optional[ruamel.yaml.YAML] = None,
):
    """Decorator to mark a function as the representer for a certain type"""

    def wrapper(representer: RepresenterFunc):
        add_representer(t, representer, tag=tag, _yaml=_yaml)
        return representer

    return wrapper


def is_constructor(
    tag: str,
    *,
    aliases: List[str] = None,
    hint: Union[str, Tuple[Callable[[Exception], bool], str]] = None,
    _yaml: Optional[ruamel.yaml.YAML] = None,
):
    """Decorator to mark a function as being a constructor for the given tag"""

    def wrapper(constructor: ConstructorFunc):
        add_constructor(
            tag, constructor, aliases=aliases, hint=hint, _yaml=_yaml
        )
        return constructor

    return wrapper
