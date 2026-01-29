# module_manager.py
import sys

from typing import Sequence

from importlib import import_module

from ezmodulemanager.libutils import parse_traceback
from ezmodulemanager.exceptions import MissingModuleError



def import_modlist(modlist: Sequence[str]) -> None:
    """Import modules sequentially.

    :param modlist: A tuple of module names to register with the
        :attr:`_REGISTRY`. Each module name is input without the '.py'
        extension.
        This includes two types of modules:

        - Modules that want to store functions with :attr:`_REGISTRY`.
        - Modules that want to use functions stored with :attr:`_REGISTRY`.

    :raises MissingModuleError: If a module in `modlist` cannot be found.
    """
    try:
        for module in modlist:
            _IMPORTED_MODULE = import_module(module)
            # print('Imported Module:', _IMPORTED_MODULE.__name__)

    except ModuleNotFoundError:
        parse_traceback()
        raise sys.exit(MissingModuleError()) # pyright: ignore
