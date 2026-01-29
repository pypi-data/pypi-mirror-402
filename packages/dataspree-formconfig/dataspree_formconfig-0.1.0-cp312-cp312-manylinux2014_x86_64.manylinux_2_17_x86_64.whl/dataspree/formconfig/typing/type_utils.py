"""Typing utilities."""

from logging import getLogger
from typing import Any, TypeVar, cast, get_args, get_origin, overload, runtime_checkable, Protocol, Type
from typing_extensions import Never

from dataspree.formconfig.core.exceptions import FormConfigImplementationError, FormConfigUserError
from dataspree.formconfig.core.naming import python_identifier_to_type_key
from dataspree.formconfig.data.base import BaseContent


logger = getLogger(__name__)


def type_args_of(tp: Any, *, of: Any | None = None) -> tuple[Any, ...]:
    """Return type arguments for a typing alias or a subclass of a generic.

    If `of` is provided, prefer/return args from the base whose origin is `of`.
    Falls back to the first parameterized base found. Returns () if none.
    """
    # Case 0: GenericWithArgs-style parametrized subclasses (dynamic subclasses)
    origin = getattr(tp, '__origin__', None)
    type_args = getattr(tp, '__type_args__', None)
    if type_args is not None:
        if of is None:
            return cast(tuple[Any, ...], type_args)
        if origin is of:
            return cast(tuple[Any, ...], type_args)

    # Case 1: direct typing alias like List[int], ConfigList[Foo], etc.
    direct_args = get_args(tp)
    if direct_args:
        if of is None or get_origin(tp) is of:
            return direct_args

    # Case 2: walk the class hierarchy and inspect parameterized bases
    # (__orig_bases__) to find concrete args used in the subclass.
    mro = getattr(tp, '__mro__', (tp,))
    for cls in mro:
        for base in getattr(cls, '__orig_bases__', ()):
            origin = get_origin(base)
            args = get_args(base)
            if not args:
                continue
            if of is None or origin is of:
                return args

    # Nothing found
    return ()


def resolve_generic_arg(tp: Any, *, index: int = 0, default: Any = Any, of: Any | None = None) -> Any:
    """Resolve a single generic argument at `index` from `tp`.

    Works for both typing aliases and subclasses of generics.
    Use `of` to target a specific generic origin if `tp` has multiple.
    """
    args = type_args_of(tp, of=of)
    return args[index] if len(args) > index else default


def resolve_generic_args(tp: Any, *, of: Any | None = None) -> tuple[Any, ...]:
    """Resolve generic arguments.

    Works for both typing aliases and subclasses of generics.
    Use `of` to target a specific generic origin if `tp` has multiple.
    """
    return type_args_of(tp, of=of)


_TSupports = TypeVar('_TSupports', bound='SupportsTypeKey')


@runtime_checkable
class SupportsTypeKey(Protocol):
    """Protocol for classes that support a type key classmethod."""

    @classmethod
    def type_key(cls: Type[_TSupports]) -> str:
        """Return the string identifier of the type, used for Union dispatch."""


@overload
def type_key(bc: Type[Any]) -> Never: ...


@overload
def type_key(bc: BaseContent | object) -> str: ...


def type_key(bc: BaseContent | object) -> str:
    """Return the type key for a non-class value."""
    if isinstance(bc, type):
        raise FormConfigImplementationError(f'The function type_key expects an instance, not a type {bc}.')
    return type_key_class(type(bc))


def type_key_class(tp: Type[Any] | str) -> str:
    """Return the type key of an arbitrary type.

    Uses the implementation of type_key if it is a base content, and a version of the type name otherwise.
    """
    if isinstance(tp, str):
        return python_identifier_to_type_key(tp)

    try:
        if issubclass(tp, SupportsTypeKey):
            return tp.type_key()
    except TypeError:
        raise FormConfigImplementationError(f'Invalid type key lookup: {tp}')

    return python_identifier_to_type_key(tp.__name__)


__get_implementation_type = TypeVar('__get_implementation_type')


def get_implementation(
    super_class: Type[__get_implementation_type],
    sub_class_name: str | None,
    default: Type[__get_implementation_type] | None = None,
    ignore_list: list[Type[__get_implementation_type]] | None = None,
    continue_multiple: bool = False,
) -> Type[__get_implementation_type]:
    """Return the subclass of #super_class that match the #sub_class_name."""
    candidates: list[Type[__get_implementation_type]] = get_implementations(
        super_class=super_class, sub_class_name=sub_class_name, ignore_list=ignore_list
    )
    if len(candidates) > 1:
        msg = f"Name ambiguity for {super_class}'s subclasses: Multiple candidates {candidates} for {sub_class_name}."
        if not continue_multiple:
            raise FormConfigImplementationError(msg)
        logger.warning(msg)

    elif len(candidates) == 0:
        if default is not None:
            return default

        if hasattr(super_class, 'default'):
            try:
                default = getattr(super_class, 'default')()
                if default is not None and issubclass(default, super_class):
                    return default
            except (TypeError, ValueError):
                pass

        raise FormConfigUserError(f'Class for {sub_class_name} not found.')

    return candidates[0]


def get_implementations(
    super_class: Type[__get_implementation_type],
    sub_class_name: str | None = None,
    ignore_list: list[Type[__get_implementation_type]] | None = None,
) -> list[Type[__get_implementation_type]]:
    """Return list of subclasses of #super_class that match the #sub_class_name.

    If there is no naming ambiguity (*) , the returned list is either empty if the subclass is not
    found, or contains exactly one entry.

    (*) Naming ambiguities can arise if the developers discard the naming convention, and provide
    two subclasses of the same super_class, one of which following a camel case and the other
    one a snake case naming convention.
    """
    if ignore_list is None:
        ignore_list = list()

    return [
        a
        for a in subclasses(super_class)
        if a not in ignore_list and (sub_class_name is None or type_key_class(a) == sub_class_name)
    ]


__subclasses_tv = TypeVar('__subclasses_tv')


def subclasses(super_class: Type[__subclasses_tv]) -> set[Type[__subclasses_tv]]:
    """Iteratively gather all descendents (allowing for multiple levels of inheritance) of the provided #super_class."""
    if not hasattr(super_class, '__subclasses__'):
        return set()

    list_subclasses: list[Type[__subclasses_tv]] = super_class.__subclasses__()
    checked_types: set[type] = set()
    i: int = 0
    while i < len(list_subclasses):
        curr = list_subclasses[i]
        if curr not in checked_types:
            checked_types.add(curr)
            list_subclasses.extend(curr.__subclasses__())
        i += 1

    return set(list_subclasses)
