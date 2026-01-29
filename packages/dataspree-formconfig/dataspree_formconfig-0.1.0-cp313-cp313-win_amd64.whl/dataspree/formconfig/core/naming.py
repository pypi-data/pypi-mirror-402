"""Utils that are useful for consistent log messages."""

from typing import Any

import re


def display_class_name(a: Any) -> str:
    """Return a human-readable name for a class type.

    Used in order to keep the same representation for classes.
    """
    # Accept typing aliases (TypeForm / GenericAlias / etc.) as well.

    try:
        # Prefer option A: return a.__name__ Pretty class name (str, or A if the class is created via class A: ...
        # Possible Alternative: return a.__qualname__. Same as A, but gives nested classes as well (A.B).
        name = getattr(a, '__name__')
        if isinstance(name, str) and name:
            return name
    except Exception:
        pass

    # Return repr(A). More meaningful because it contains information on the module etc, but looks messier.
    return repr(a)


def display_value(value: Any, value_length: int = 25) -> str:
    """Display a value as a human-readable string that is truncated in order to not flood the logs."""
    try:
        return (rep := repr(value))[:value_length] + (' (truncated)' if len(rep) > value_length else '')
    except AttributeError as e:
        # Raised if repr(value) raises, which can be the case in multiple circumstances
        # (f.i., not completely initialized dataclass etc.
        return repr(e)


def python_identifier_to_type_key(name: str) -> str:
    """Convert CamelCase or mixedCase identifiers to snake_case.

    Rules:
    - Treat existing underscores as word boundaries.
    - Do not introduce duplicate underscores.
    - Preserve leading underscores.
    - Lowercase the result.
    """
    if not name:
        return name

    # Preserve leading underscores
    leading = re.match(r'^_+', name)
    prefix = leading.group(0) if leading else ''
    core = name[len(prefix) :]

    # Replace transitions from lower/number to upper: fooBar -> foo_bar
    core = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', core)

    # Replace transitions in acronyms: HTTPServer -> HTTP_Server
    core = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', core)

    # Normalize existing underscores to single underscores
    core = re.sub(r'_+', '_', core)

    return prefix + core.lower()
