# exceptions.py

# Base Class
class ModManagerError(Exception):
    """Base exception class for the Mod Manager package."""

    def __init__(self, msg=None):

        if msg == None:
            msg = ('ModManagerError: A default error has occured. '
            'Please copy the traceback summary from the terminal '
            'and paste the traceback summary into the Github '
            'issue tracker.'
            )

        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return self.msg


# Sub-classes

## register_obj() exceptions
class ObjectRegistrationError(ModManagerError):
    """Raised when not passing a valid object"""
    def __init__(self):

        msg = ('(ObjectRegistrationError) A pruned stack summary has '
        'been output. You can see each `stack trace` in '
        'ascending order starting from `Stack Trace (1)`. \n')
        'Make sure that all `register_obj()` functions are '
        'passing valid objects as arguments and not str literals.'
        super().__init__(msg)


## get_obj() exceptions
class RegistryKeyError(ModManagerError):
    """Raised when a requested objects's key is not found in the
    `_REGISTRY`'s `dict{}`."""
    def __init__(self):

        msg = ('(RegistryKeyError) A pruned stack summary has '
        'been output. You can see each `stack trace` in '
        'ascending order starting from `Stack Trace (1)`. \n'
        'The idea is to find the offending function(eg., `get_obj()`) '
        'which most likely has a mispelled argument. \n'
        'If the arguments are spelled correctly, '
        'make sure that you have actually registered the objects '
        'you are trying \nto get with `@mmreg` or `register_obj()`. \n'
        'Still have questions or problems? My contact info is on PyPI!'
        )

        super().__init__(msg)



## import_modlist() exceptions

class MissingModuleError(ModManagerError):
    """Raised when `import_modlist()` cant find a specified module."""
    def __init__(self):


        msg = ('A Module was not found by `import_modlist()` '
        ' Please check the spelling of all imported modules.'
        )

        super().__init__(msg)
