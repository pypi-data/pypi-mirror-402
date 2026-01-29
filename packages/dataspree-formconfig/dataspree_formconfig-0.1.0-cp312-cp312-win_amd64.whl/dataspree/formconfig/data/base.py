"""Defines the minimal content abstraction (BaseContent).

The BaseContent contains helpers for child lookup, type tags, and union key resolution.
It's a lightweight interface that all configurable data implements so the field layer can traverse and inspect values.
"""

from __future__ import annotations

from abc import ABC
from typing import TypeAlias, get_args, Type

from dataspree.formconfig.core.exceptions import FormConfigImplementationError
from dataspree.formconfig.core.naming import python_identifier_to_type_key

PrimitiveTypes = int | bool | str | float

PrimitiveArgs: tuple[Type[int], Type[bool], Type[str], Type[float]] = (int, bool, str, float)

if set(PrimitiveArgs) != set(get_args(PrimitiveTypes)):
    raise FormConfigImplementationError('PrimitiveTypes must be a typing.Union of concrete primitive classes.')


PrimitiveClass: TypeAlias = Type[int] | Type[bool] | Type[str] | Type[float]


class BaseContent(ABC):
    """The base content abstraction that is visualized by a BaseField.

    Contains things that can be contained in a BaseField.

    Has got an identifier that allows the UI elements to visualize the correct options (e.g. in case of a Union).
    """

    @classmethod
    def type_key(cls) -> str:
        """Return the string identifier of the type, used for Union dispatch."""
        return python_identifier_to_type_key(cls.__name__)
