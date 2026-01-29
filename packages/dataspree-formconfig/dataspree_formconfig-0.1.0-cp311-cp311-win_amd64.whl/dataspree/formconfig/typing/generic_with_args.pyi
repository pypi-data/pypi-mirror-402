import types
from typing import Any

class GenericWithArgs:
    """Allows instances of generic types to remember their type args.

    This is done by returning a custom subclass for each Generics they receive.
    Isinstance checks still work.

    Usage: Inherit from GenericWithArg.
    """
    __type_args__: tuple[Any, ...] | None
    __origin__: type[GenericWithArgs] | None
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Raise an error if the GenericsWithArgs implementation is not parametrized."""
    def __init_subclass__(cls) -> None:
        """Initialize the subclass and store the origin."""
    @classmethod
    def typing_alias(cls) -> types.GenericAlias:
        """Return a generic type alias for this class."""
    @classmethod
    def __class_getitem__(cls, item: Any) -> type[GenericWithArgs]:
        """Instantiate class with generics ensuring isinstance checks work."""
