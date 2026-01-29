"""Reading and writing YAML files"""

import io
import logging
import os
from typing import Any, Union

import ruamel.yaml

from .exceptions import (
    YAML_ERROR_HINTS,
    RepresenterError,
    raise_improved_exception,
)
from .yaml import yaml

log = logging.getLogger(__name__)

# -- Writing and reading from files -------------------------------------------


def load_yml(
    path: str,
    *,
    mode: str = "r",
    encoding: str = "utf8",
    improve_errors: bool = True,
    _yaml: ruamel.yaml.YAML = yaml,
) -> Any:
    """Deserializes a YAML file into a Python object.

    Uses the yayaml-internal ``ruamel.yaml.YAML`` object for loading and thus
    supports all registered constructors.

    Args:
        path (str): The path to the YAML file that should be loaded. A ``~`` in
            the path will be expanded to the current user's directory.
        mode (str, optional): Read mode for the file at ``path``
        encoding (str, optional): The encoding to use. Assumes UTF-8 as the
            default; however, if there is a ``UnicodeDecodeError``, will try
            again with ``encoding=None``, thus using the default encoding of
            the operating system.
        improve_errors (bool, optional): Whether to improve error messages that
            come from the call to ``yaml.load``. If true, the error message
            is inspected and hints are appended.
        _yaml (ruamel.yaml.YAML, optional): If given, will use this YAML object
            for loading. By default, the yayaml-internal one is used, which
            supports all registered constructors.

    Returns:
        Any: The result of the data loading. Typically, this will be a dict,
            but depending on the structure of the file, it may be some other
            type, including ``None``.
    """
    path = os.path.expanduser(path)
    log.debug("Loading YAML file... mode: %s, path:\n  %s", mode, path)

    with open(path, mode, encoding=encoding) as yaml_file:
        try:
            return _yaml.load(yaml_file)

        except (ruamel.yaml.reader.ReaderError, UnicodeDecodeError):
            return load_yml(
                path,
                mode=mode,
                encoding=None,
                improve_errors=improve_errors,
                _yaml=_yaml,
            )

        except Exception as exc:
            if not improve_errors:
                raise

            # Attempt raising a new and improved error message.
            # Will simply re-raise if that is not the case.
            raise_improved_exception(exc, hints=YAML_ERROR_HINTS)


def write_yml(
    d: Union[dict, Any],
    *,
    path: str,
    mode: str = "w",
    _yaml: ruamel.yaml.YAML = yaml,
):
    """Serialize an object using YAML and store it in a file.

    Uses the dantro-internal ``ruamel.yaml.YAML`` object for dumping and thus
    supports all registered representers.

    Args:
        d (dict): The object to serialize and write to file
        path (str): The path to write the YAML output to. A ``~`` in the path
            will be expanded to the current user's directory.
        mode (str, optional): Write mode of the file
    """
    path = os.path.expanduser(path)
    log.debug(
        "Dumping %s to YAML file... mode: %s, path:\n  %s",
        type(d).__name__,
        mode,
        path,
    )

    # Make sure the directory is present
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, mode) as yaml_file:
        # Add the yaml '---' prefix, then dump
        yaml_file.write("---\n")
        _yaml.dump(d, stream=yaml_file)
        yaml_file.write("\n")


# -- Serialization ------------------------------------------------------------


def yaml_dumps(
    obj: Any,
    *,
    register_classes: tuple = (),
    _yaml: ruamel.yaml.YAML = yaml,
    **dump_params,
) -> str:
    """Serializes the given object using (by default) yayaml's YAML object.

    Args:
        obj (Any): The object to dump
        register_classes (tuple, optional): Additional classes to register
        _yaml (ruamel.yaml.YAML, optional): Which YAML object to use for
            dumping
        **dump_params: Dumping parameters, which will be used to set the
            attributes of the given YAML object.

    Returns:
        str: The output of serialization

    Raises:
        RepresenterError: On failure to serialize the given
            object
    """
    s = io.StringIO()
    y = _yaml

    # Register classes; then apply dumping parameters via object properties
    for Cls in register_classes:
        y.register_class(Cls)

    for k, v in dump_params.items():
        setattr(y, k, v)

    # Serialize
    try:
        y.dump(obj, stream=s)

    except Exception as err:
        raise RepresenterError(
            f"Could not serialize the given {type(obj)} object!"
        ) from err

    return s.getvalue()


def yaml_dumps_plain(*args, **kwargs):
    """Like :py:func:`.yaml_dumps` but will create a completely new
    ``ruamel.yaml.YAML`` object for dumping, thus not having any of the special
    constructors and representers registered.

    The aim of this function is to provide YAML dumping that is not dependent
    on any package configuration; all parameters can be passed here.

    In other words, this function does _not_ use the yayaml's YAML object
    for dumping but each time creates a new dumper with fixed settings.
    This reduces the chance of interference from elsewhere.
    Compared to the time needed for serialization in itself, the extra time
    needed to create the new ruamel.yaml.YAML object and register the classes
    is negligible.

    .. hint::

        To use yayaml's YAML object, use :py:func:`.yaml_dumps` instead.

    .. note::

        The new YAML object will not have _any_ additional representers
        available!
    """
    return yaml_dumps(*args, **kwargs, _yaml=ruamel.yaml.YAML())
