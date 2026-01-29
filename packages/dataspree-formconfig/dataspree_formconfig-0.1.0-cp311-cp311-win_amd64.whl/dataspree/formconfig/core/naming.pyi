from typing import Any

def display_class_name(a: Any) -> str:
    """Return a human-readable name for a class type.

    Used in order to keep the same representation for classes.
    """
def display_value(value: Any, value_length: int = 25) -> str:
    """Display a value as a human-readable string that is truncated in order to not flood the logs."""
def python_identifier_to_type_key(name: str) -> str:
    """Convert CamelCase or mixedCase identifiers to snake_case.

    Rules:
    - Treat existing underscores as word boundaries.
    - Do not introduce duplicate underscores.
    - Preserve leading underscores.
    - Lowercase the result.
    """
