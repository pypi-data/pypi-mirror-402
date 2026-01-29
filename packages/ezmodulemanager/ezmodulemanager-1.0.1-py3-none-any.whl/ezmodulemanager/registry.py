# registry.py
import sys
import os
import pathlib

from typing import Any, Callable, Mapping

from ezmodulemanager.libutils import parse_traceback
from ezmodulemanager.exceptions import RegistryKeyError, ObjectRegistrationError


_REGISTRY = {}


def mmreg(obj: Any)-> Callable[..., Any]:
    """Store an object in the `_Registry` as a decorator.

    `@mmreg` automatically stores the containing modules namespace
    as a key for the outermost `dict`. It then stores the object name as
    a key for the innermost `dict`. Last but not least, it stores the
    reference of the object as the value for that
    innermost `dict`. You can then use that reference to
    call on that object.

    :param obj: The object to store in the `_REGISTRY`.
    """
    # if the module that contains the object is not in the
    # `_REGISTRY`, add the `__module__` as a key with an empty `dict`.
    if obj.__module__ not in _REGISTRY:
        _REGISTRY[obj.__module__] = {}
    # Then add the object reference as a value to the object `__name__` key.
    _REGISTRY[obj.__module__][obj.__name__] = obj
    return obj

def query_registry()-> Mapping[str, Mapping[str, Any]]:
    """Query the `_REGISTRY` global for entries.

    :returns: Returns a raw query of nested dictionaries within
        the `_REGISTRY`. Each module has its own `dict` which
        contains all objects within its own namespace that are
        registered with the `_REGISTRY`.
    """
    return _REGISTRY


def register_obj(obj: Any, obj_name: str, mod_path: str) -> None:
    """Stores a variable-type object in the `_REGISTRY`.

    `register_obj()` does the same exact thing as `mmreg()`,
    except this allows the control over manual 'registration'
    from a modular standpoint.

    :param obj: The object itself to store in the `_REGISTRY`.
    :param obj_name: The str literal to name the object you are
        'registering'. This acts as the key lookup in the `dict`.
    :param mod_path: This will always be `__file__`. The attribute is
        only avaialble from the module its called from.

    :raises: ObjectRegistrationError: Raised if `register_obj()' is
        NOT passing a valid object. Usually when an object
        registration attempt is done using a str literal.
    """
    # Get stemmed pure path for `registry` key.
    if os.name == 'posix':
        mod_name = pathlib.PurePosixPath(mod_path).stem
    elif os.name == 'nt':
        mod_name = pathlib.PureWindowsPath(mod_path).stem
    else:
        raise OSError

    try:
        if mod_name not in _REGISTRY:
            _REGISTRY[mod_name] = {}
        _REGISTRY[mod_name][obj_name] = obj
    except (AttributeError):
        parse_traceback()
        raise sys.exit(ObjectRegistrationError()) # pyright: ignore


def get_obj(
    module_name: str,
    obj_name: str,
    *args: Any
) -> Any:
    """Retrieves an object that has been stored in the `_REGISTRY`.

    :param module_name: The module namespace whose object you
        want access to.
    :param obj_name: The name of the object within the `module_name`
        to access.
    :param *args: Variable positional arguments passed to the registered
        object. If provided, the object is executed immediately.
    
    :returns: If no arguments are provided, it returns a reference
        to the object itself.
    :returns: If arguments are provided, it executes the object immediately,
        and returns `Any` return value from the executed object.

    :raises: RegistryKeyError: Raised if `module_name` or `obj_name` does
        not exist in the `registry` component.
    """
    try:
        # Call will always be True if there are arguments.
        if args:
            # Calls the parameterized object and returns Any.
            return _REGISTRY[module_name][obj_name](*args)
        else:
            # Returns the object itself, Any.
            return _REGISTRY[module_name][obj_name]
    except KeyError:
        parse_traceback()
        raise sys.exit(RegistryKeyError()) # pyright: ignore
