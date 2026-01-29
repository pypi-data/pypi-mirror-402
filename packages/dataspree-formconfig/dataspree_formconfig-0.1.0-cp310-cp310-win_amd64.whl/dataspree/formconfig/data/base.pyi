from abc import ABC
from typing import TypeAlias

PrimitiveTypes = int | bool | str | float
PrimitiveArgs: tuple[type[int], type[bool], type[str], type[float]]
PrimitiveClass: TypeAlias = type[int] | type[bool] | type[str] | type[float]

class BaseContent(ABC):
    """The base content abstraction that is visualized by a BaseField.

    Contains things that can be contained in a BaseField.

    Has got an identifier that allows the UI elements to visualize the correct options (e.g. in case of a Union).
    """
    @classmethod
    def type_key(cls) -> str:
        """Return the string identifier of the type, used for Union dispatch."""
