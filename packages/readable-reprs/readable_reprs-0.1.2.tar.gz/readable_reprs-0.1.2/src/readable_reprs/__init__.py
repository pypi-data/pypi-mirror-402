from enum import Enum
from functools import wraps


def patch_reprs() -> None:
    """
    Patch the reprs of existing types so that the string representation is valid Python code.

    Must be called before the program imports those types (even transitively). It's a good
    idea to call this before any other imports at the top of your main Python file.

    This currently patches:
    - `enum.Enum`
    """
    _patch_enum()


def _patch_enum() -> None:
    @wraps(Enum.__repr__)
    def patched_repr(self):
        return f"{self.__class__.__name__}.{self.name}"

    Enum.__repr__ = patched_repr
