from _typeshed import Incomplete
from dataspree.formconfig.data.base import BaseContent as BaseContent
from typing import Any, Protocol, overload
from typing_extensions import Never

logger: Incomplete

def type_args_of(tp: Any, *, of: Any | None = None) -> tuple[Any, ...]:
    """Return type arguments for a typing alias or a subclass of a generic.

    If `of` is provided, prefer/return args from the base whose origin is `of`.
    Falls back to the first parameterized base found. Returns () if none.
    """
def resolve_generic_arg(tp: Any, *, index: int = 0, default: Any = ..., of: Any | None = None) -> Any:
    """Resolve a single generic argument at `index` from `tp`.

    Works for both typing aliases and subclasses of generics.
    Use `of` to target a specific generic origin if `tp` has multiple.
    """
def resolve_generic_args(tp: Any, *, of: Any | None = None) -> tuple[Any, ...]:
    """Resolve generic arguments.

    Works for both typing aliases and subclasses of generics.
    Use `of` to target a specific generic origin if `tp` has multiple.
    """

class SupportsTypeKey(Protocol):
    """Protocol for classes that support a type key classmethod."""
    @classmethod
    def type_key(cls) -> str:
        """Return the string identifier of the type, used for Union dispatch."""

@overload
def type_key(bc: type[Any]) -> Never: ...
@overload
def type_key(bc: BaseContent | object) -> str: ...
def type_key_class(tp: type[Any] | str) -> str:
    """Return the type key of an arbitrary type.

    Uses the implementation of type_key if it is a base content, and a version of the type name otherwise.
    """
def get_implementation(super_class: type[__get_implementation_type], sub_class_name: str | None, default: type[__get_implementation_type] | None = None, ignore_list: list[type[__get_implementation_type]] | None = None, continue_multiple: bool = False) -> type[__get_implementation_type]:
    """Return the subclass of #super_class that match the #sub_class_name."""
def get_implementations(super_class: type[__get_implementation_type], sub_class_name: str | None = None, ignore_list: list[type[__get_implementation_type]] | None = None) -> list[type[__get_implementation_type]]:
    """Return list of subclasses of #super_class that match the #sub_class_name.

    If there is no naming ambiguity (*) , the returned list is either empty if the subclass is not
    found, or contains exactly one entry.

    (*) Naming ambiguities can arise if the developers discard the naming convention, and provide
    two subclasses of the same super_class, one of which following a camel case and the other
    one a snake case naming convention.
    """
def subclasses(super_class: type[__subclasses_tv]) -> set[type[__subclasses_tv]]:
    """Iteratively gather all descendents (allowing for multiple levels of inheritance) of the provided #super_class."""
