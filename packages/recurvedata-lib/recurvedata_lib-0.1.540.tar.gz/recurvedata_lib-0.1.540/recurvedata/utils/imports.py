"""
This module is a copy of the import_string function from Sentry.
"""

from __future__ import annotations

from typing import Callable, Type


class ModuleProxyCache(dict):
    def __missing__(self, key):
        if "." not in key:
            return __import__(key)

        module_name, class_name = key.rsplit(".", 1)

        module = __import__(module_name, {}, {}, [class_name])
        handler = getattr(module, class_name)

        # We cache a NoneType for missing imports to avoid repeated lookups
        self[key] = handler

        return handler


_cache = ModuleProxyCache()


def import_string(path: str) -> Type:
    """
    Path must be module.path.ClassName

    >>> cls = import_string('sentry.models.Group')
    """
    result = _cache[path]
    return result


# This is a copy of the qualname function from Apache Airflow.
def qualname(o: object | Callable) -> str:
    """Convert an attribute/class/function to a string importable by ``import_string``."""
    if callable(o) and hasattr(o, "__module__") and hasattr(o, "__name__"):
        return f"{o.__module__}.{o.__name__}"

    cls = o

    if not isinstance(cls, type):  # instance or class
        cls = type(cls)

    name = cls.__qualname__
    module = cls.__module__

    if module and module != "__builtin__":
        return f"{module}.{name}"

    return name


class MockModule:
    """
    A placeholder object for handling failed module imports.
    When attempting to access any attribute or call any method on this object,
    it will raise an ImportError exception to notify the user that the module
    was not successfully imported.

    Usage example:
    ```
    try:
        import some_module
    except ImportError:
        some_module = MockModule("some_module")

    # When trying to use some_module, it will raise an import error
    some_module.some_function()  # Will raise ImportError
    ```
    """

    def __init__(self, module_name):
        self.__module_name = module_name

    def __getattr__(self, name):
        """Triggered when accessing any attribute"""
        self.__raise_import_error()

    def __call__(self, *args, **kwargs):
        """Triggered when attempting to call as a function"""
        self.__raise_import_error()

    def __getitem__(self, key):
        """Triggered when attempting to access as dictionary or list"""
        self.__raise_import_error()

    def __raise_import_error(self):
        """Raise standard import error"""
        raise ImportError(
            f"Module '{self.__module_name}' was not successfully imported. Please install the module before using it."
        )


class MockDecorator:
    """
    A decorator that raises ImportError when the decorated function is called.

    This is useful for creating placeholder decorators for optional dependencies.
    The ImportError is only raised when the decorated function is actually called,
    not when the module is imported or the function is defined.

    Usage example:
    ```
    try:
        from optional_package import some_decorator
    except ImportError:
        some_decorator = MockDecorator("optional_package")

    @some_decorator
    def my_function():
        pass

    # The ImportError will only be raised when my_function is called, not when it's defined
    ```
    """

    def __init__(self, module_name):
        self.__module_name = module_name

    def __call__(self, func, *args, **kwargs):
        def wrapper(*args, **kwargs):
            raise ImportError(
                f"Module '{self.__module_name}' was not successfully imported. Please install the module before using it."
            )

        return wrapper
