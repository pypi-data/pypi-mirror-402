"""Provides a class that allows instances of generic types to remember their type args."""

from __future__ import annotations

import types
import weakref
import threading

from typing import Any, cast, Type

from dataspree.formconfig.core.exceptions import FormConfigTypeResolutionError


class GenericWithArgs:
    """Allows instances of generic types to remember their type args.

    This is done by returning a custom subclass for each Generics they receive.
    Isinstance checks still work.

    Usage: Inherit from GenericWithArg.
    """

    __type_args__: tuple[Any, ...] | None = None
    __origin__: Type[GenericWithArgs] | None = None
    _cache: weakref.WeakValueDictionary[
        tuple[Type[GenericWithArgs], tuple[Any, ...]],
        Type[GenericWithArgs],
    ] = weakref.WeakValueDictionary()
    _lock = threading.Lock()

    def __init__(self: GenericWithArgs, *args: Any, **kwargs: Any) -> None:
        """Raise an error if the GenericsWithArgs implementation is not parametrized."""
        super().__init__(*args, **kwargs)
        if self.__type_args__ is None:
            origin = self.__origin__ or type(self)
            # We could also just warn here, because in most cases it is possible to recover / this is not really
            # needed because we can use the generics from the content. But We don't really know here how this is used
            # and just warning would make this a bit more complicated for allowing laziness during typing.
            raise FormConfigTypeResolutionError(
                f'{origin.__name__} must be parametrized, e.g. {origin.__name__}[T](...).'
            )

    def __init_subclass__(cls) -> None:
        """Initialize the subclass and store the origin."""
        super().__init_subclass__()
        cls.__origin__ = cls.__origin__ or cls

    @classmethod
    def typing_alias(cls: Type[GenericWithArgs]) -> types.GenericAlias:
        """Return a generic type alias for this class."""
        origin: Type[GenericWithArgs] = cls.__origin__ or cls
        args = cls.__type_args__
        if args is None:
            raise FormConfigTypeResolutionError(f'{origin.__name__} is not parametrized.')
        if len(args) == 1:
            return types.GenericAlias(origin, args[0])
        return types.GenericAlias(origin, args)

    @classmethod
    def __class_getitem__(cls: Type[GenericWithArgs], item: Any) -> Type[GenericWithArgs]:
        """Instantiate class with generics ensuring isinstance checks work."""
        args = item if isinstance(item, tuple) else (item,)
        origin: Type[GenericWithArgs] = cls.__origin__ or cls
        key = (origin, args)
        if (cached := origin._cache.get(key)) is not None:
            return cached

        def body(ns: dict[str, Any]) -> None:
            ns['__origin__'] = origin
            ns['__type_args__'] = args

        with origin._lock:
            if (cached := origin._cache.get(key)) is not None:
                return cached

            sub = types.new_class(f'{origin.__name__}[...]', (origin,), exec_body=body)
            sub.__module__ = origin.__module__

            typed_sub = cast(Type[GenericWithArgs], sub)
            origin._cache[key] = typed_sub
            return typed_sub
