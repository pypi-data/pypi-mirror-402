"""General parsing functionality that can deal with primitive types and BaseConfigurables."""

from __future__ import annotations

# Local type vars for container shapes
from types import UnionType
from typing import TypeVar, overload, Any, cast, get_origin, Union, get_args, TYPE_CHECKING, Type

from enum import Enum
from typing_extensions import TypeForm
from warnings import warn

from dataspree.formconfig.data.base import PrimitiveArgs
from dataspree.formconfig.data.base_configurable import (
    BaseConfigurableData,
    AliasContainerType,
    WrapperAlias,
    ConfigValue,
)

if TYPE_CHECKING:
    from dataspree.formconfig.data.config_list import ConfigList
    from dataspree.formconfig.data.config_optional import ConfigOptional
    from dataspree.formconfig.data.config_union import ConfigUnion


from dataspree.formconfig.core.exceptions import (
    FormConfigError,
    FormConfigUserError,
    FormConfigParseError,
    FormConfigTypeResolutionError,
)
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.typing.type_utils import get_implementation, resolve_generic_arg, type_key_class

CT = TypeVar('CT', bound=ConfigValue)
K = TypeVar('K')
V = TypeVar('V')

# Local type vars matching your generic wrappers
CU = TypeVar('CU', bound=ConfigValue)
CO = TypeVar('CO', bound=ConfigValue)
L = TypeVar('L', bound=ConfigValue)


@overload
def from_defaults(alias: str, data: Any) -> BaseConfigurableData | Any:
    # Resolve a string alias to a BaseConfigurableData subclass and parse via that implementation.
    #
    # Captures calls like:
    #     from_defaults(alias="MyConfigData", data={...})
    #
    # Notes:
    #     If the string looks generic (contains list[...] / Union / | / etc), the implementation raises.
    #     Otherwise, it resolves via get_implementation(BaseConfigurableData, alias) and dispatches.
    ...


@overload
def from_defaults(alias: Type[BaseConfigurableData], data: Any) -> BaseConfigurableData:
    # Parse when alias is a concrete BaseConfigurableData subclass.
    #
    # Captures calls like:
    #     from_defaults(alias=MyConfigData, data={...})
    #
    # Notes:
    #     This dispatches to alias.from_defaults(data=..., alias=alias).
    #     Return type is BaseConfigurableData at type level (the concrete subtype at runtime).
    ...


@overload
def from_defaults(alias: TypeForm[ConfigUnion[CU]], data: Any) -> ConfigUnion[CU]:
    # Parse when alias is ConfigUnion[CU].
    #
    # Captures calls like:
    #     from_defaults(alias=ConfigUnion[int | MyCfg], data={...})
    #
    # Notes:
    #     This returns a ConfigUnion instance whose .content is parsed based on the selection.
    #     The selection must match one of the union member type keys.
    ...


@overload
def from_defaults(alias: TypeForm[ConfigOptional[CO]], data: Any) -> ConfigOptional[CO]:
    # Parse when alias is ConfigOptional[CO].
    #
    # Captures calls like:
    #     from_defaults(alias=ConfigOptional[int], data={"default": True, "content": 3})
    #
    # Notes:
    #     This returns a ConfigOptional instance.
    #     If data["default"] is falsy, the returned instance has content=None.
    #     If enabled, content is parsed recursively using the inner alias.
    ...


@overload
def from_defaults(alias: TypeForm[ConfigList[L]], data: Any) -> ConfigList[L]:
    # Parse when alias is ConfigList[L].
    #
    # Captures calls like:
    #     from_defaults(alias=ConfigList[int], data=[{"content": 1}, {"content": 2}])
    #
    # Notes:
    #     This returns a ConfigList instance (your list subclass).
    #     Each row may be either {"content": ...} or a direct value; both are supported.
    ...


@overload
def from_defaults(alias: TypeForm[list[CT]], data: Any) -> ConfigList[CT]:
    # Parse when alias is a raw list[CT] typing alias.
    #
    # Captures calls like:
    #     from_defaults(alias=list[int], data=[1, 2])
    #     from_defaults(alias=list[MyCfg], data=[{...}, {...}])
    #
    # Notes:
    #     Your implementation converts list[...] into ConfigList.from_defaults(...).
    #     Therefore the runtime result is a ConfigList, not a plain Python list.
    #     (This branch also emits a warning in your implementation.)
    ...


@overload
def from_defaults(alias: TypeForm[tuple[CT, ...]], data: Any) -> tuple[Any, ...]:
    # Parse when alias is tuple[CT, ...] (variadic tuple).
    #
    # Captures calls like:
    #     from_defaults(alias=tuple[int, ...], data=(1, 2, 3))
    #
    # Notes:
    #     This returns a tuple of the same length as the input data.
    #     Each element is parsed recursively using the tuple element alias.
    ...


@overload
def from_defaults(alias: TypeForm[tuple[Any, Any]], data: Any) -> tuple[Any, ...]:
    # Parse when alias is a fixed-length tuple alias.
    #
    # Captures calls like:
    #     from_defaults(alias=tuple[int, str], data=(1, "x"))
    #
    # Notes:
    #     This returns a tuple with one parsed element per alias argument.
    #     If the tuple alias is not variadic, input length must match the alias arity.
    ...


@overload
def from_defaults(alias: TypeForm[dict[K, V]], data: Any) -> dict[Any, Any]:
    # Parse when alias is dict[K, V].
    #
    # Captures calls like:
    #     from_defaults(alias=dict[str, int], data={"a": 1})
    #
    # Notes:
    #     This returns a dict whose keys and values are parsed recursively.
    #     Dict keys are additionally constrained by your implementation (primitive or ConfigEnum).
    ...


@overload
def from_defaults(alias: Any, data: Any) -> Any:
    # Fallback overload.
    #
    # Captures calls like:
    #     from_defaults(alias=SomeWeirdAlias, data=whatever)
    #
    # Notes:
    #     Anything not matched above lands here.
    #     The implementation will either return a parsed structure or raise FormConfigError.
    ...


def from_defaults(alias: Type[Any] | AliasContainerType | str, data: Any) -> Any:
    """Create an instance from UI defaults data.

    Implementation note:
        The overloads describe common call shapes. The implementation performs runtime
        dispatch based on get_origin/get_args and on whether `alias` is a BaseConfigurableData
        subclass, a container typing alias, or a string.

    Raises:
        FormConfigError: If the input cannot be parsed for this type.
    """
    # Local imports are intentional to avoid circular imports with wrappers that import parse.from_defaults.
    from dataspree.formconfig.data.config_list import ConfigList
    from dataspree.formconfig.data.config_optional import ConfigOptional
    from dataspree.formconfig.data.config_union import ConfigUnion
    from dataspree.formconfig.data.config_untyped_dict import ConfigUntypedDict

    # @dev:
    #   This is because of future __annotations__. the origin (type) is a string.
    #   However, we try to ensure that from_defaults is not called with a string and that the type is resolved earlier,
    #   because we cannot easily recover generics from the string representation.
    if isinstance(alias, str):
        warn(
            f'Passing string type annotations into from_defaults is deprecated, got {alias!r}',
            DeprecationWarning,
            stacklevel=2,
        )
        if any(tok in alias for tok in ('[', ']', '|', 'Union', 'Optional', 'list', 'dict[', 'tuple')):
            raise FormConfigError(
                f'String annotation {alias!r} is not supported here because generics cannot be recovered.'
            )

        cls = cast(Type[BaseConfigurableData], get_implementation(BaseConfigurableData, type_key_class(alias)))
        try:
            return cls.from_defaults(data=data, alias=cls)
        except FormConfigError:
            raise
        except Exception as e:
            raise FormConfigParseError(f'Failed to parse {alias} from {type(data)!r}.') from e

    #
    # Dispatch to BaseConfigurableData implementations if possible.
    #
    origin = get_origin(alias)

    # Explicitly fail for not typed list, dict tuple etc.
    if origin is None and isinstance(alias, type) and alias in (list, tuple):
        raise FormConfigError(
            f'Bare container {alias!r} is not allowed in annotations. Use ConfigList[T] or tuple[...] as appropriate.'
        )

    # Instantiate BaseConfigurableData from their method
    if isinstance(origin, type) and issubclass(origin, BaseConfigurableData):
        try:
            return origin.from_defaults(data=data, alias=alias)
        except FormConfigError:
            raise
        except Exception as e:
            raise FormConfigParseError(f'Failed to parse {display_class_name(alias)} from {type(data)!r}.') from e

    # Feature: Convert Unions automatically into ConfigUnions
    if origin in (UnionType, Union):
        args = get_args(alias)
        args_without_none_type = tuple([a for a in args if a is not type(None)])
        is_optional: bool = len(args_without_none_type) != len(args)

        if not args_without_none_type:
            raise FormConfigError('Union has no args.')

        # Create a "modern" union type, as required by ConfigUnion
        inner_args = args_without_none_type[0]
        for t in args_without_none_type[1:]:
            inner_args = inner_args | t

        used_data: dict[str, Any]
        if is_optional:
            origin = ConfigOptional
            if len(args_without_none_type) == 1:
                alias = cast(Any, ConfigOptional)[inner_args]
            else:
                alias = cast(Any, ConfigOptional)[cast(Any, ConfigUnion)[inner_args]]

            if data is None:
                used_data = {'default': False}
            elif not isinstance(data, dict) or 'default' not in data:
                used_data = {'default': True, 'content': data}
            else:
                assert isinstance(data, dict)
                used_data = data
        else:
            origin = ConfigUnion
            alias = cast(Any, ConfigUnion)[inner_args]

            if not isinstance(data, dict):
                raise FormConfigUserError('Data for ConfigUnion has to be a dict.')

            used_data = data

        try:
            return origin.from_defaults(data=used_data, alias=cast(WrapperAlias, alias))
        except FormConfigError:
            raise
        except Exception as e:
            raise FormConfigParseError(f'Failed to parse {display_class_name(alias)} from {type(data)!r}.') from e

    # Feature: Convert lists automatically into list of meaningful objects
    # @dev: We are facing an asymmetry here, because we did not add ConfigTuple as type, and are automatically
    #       converting the list[int] into the desired ConfigList[int].
    if isinstance(origin, type) and issubclass(origin, list):
        warn(
            'Passing list[...] is discouraged. Please use ConfigList[...] in the future!',
            UserWarning,
            stacklevel=2,
        )

        # Sanity check for cleaner error message
        if data is None:
            raise FormConfigError(f'None is not valid for {alias!r}. Use ConfigOptional[...] if the value is optional.')

        if not isinstance(data, list):
            raise FormConfigError(f'Expected list data for {alias!r}, got {type(data)!r}.')

        inner = resolve_generic_arg(alias, of=list, index=0, default=None)
        if inner is None or type(inner).__name__ == 'TypeVar':
            raise FormConfigError(f'Unsupported list alias {alias!r}. Please use ConfigList[T].')

        cfg_alias = cast(Any, ConfigList)[inner]
        try:
            return cfg_alias.from_defaults(data, alias=cfg_alias)
        except FormConfigError:
            raise
        except Exception as e:
            raise FormConfigError(f'Failed to parse {display_class_name(alias)} from {type(data)!r}.') from e

    # Feature: Convert tuples automatically into tuples of meaningful objects
    if isinstance(origin, type) and issubclass(origin, tuple):
        if data is None:
            raise FormConfigError(f'None is not valid for {alias!r}. Use ConfigOptional[...] if the value is optional.')

        if not isinstance(data, tuple):
            raise FormConfigError(f'Expected tuple data for {alias!r}, got {type(data)!r}.')

        args = get_args(alias)

        # Check constraints

        if Ellipsis in args:
            if len(args) != 2 or args[1] is not Ellipsis:
                raise FormConfigError(
                    f'Ellipsis argument is only allowed in conjunction with a simple type (f.i. tuple[int, ...]). '
                    f'Found {args!r} .'
                )
        else:
            if len(args) != len(data):
                raise FormConfigError(f'Expected tuple of length {len(args)} for {alias!r}, got length {len(data)}.')

        if not args:
            return tuple()

        if len(args) == 2 and args[1] is Ellipsis or len(args) == 1:  # tuple[T, ...] or tuple[T]
            return tuple(from_defaults(data=d, alias=args[0]) for d in data)

        assert args  # tuple[T1, T2, [...]]
        return tuple(from_defaults(data=d, alias=a) for d, a in zip(data, args))

    if isinstance(origin, type) and issubclass(origin, dict):
        alias_k = resolve_generic_arg(alias, index=0)
        alias_v = resolve_generic_arg(alias, index=1)

        if alias_k is None or alias_v is None:
            raise FormConfigError(f'Dict alias {alias!r} must be parametrised as dict[K, V].')

        if alias_k not in PrimitiveArgs and not (isinstance(alias_k, type) and issubclass(alias_k, Enum)):
            raise FormConfigError(
                'Dict keys must be primitive types or Enum. '
                'Other BaseConfigurableData keys are not supported because keys must be stable and JSON-like.'
            )

        if data is None:
            raise FormConfigError(
                f'Expected dict data for {alias!r}, got None. '
                'If optional, pass ConfigOptional[...] wrapper: {{"default": false}} or '
                '{{"default": true, "content": {{...}}}}.'
            )

        if not isinstance(data, dict):
            raise FormConfigError(f'Expected dict data for {alias!r}, got {type(data)!r}.')

        return {
            from_defaults(data=data_k, alias=alias_k): from_defaults(data=data_v, alias=alias_v)
            for data_k, data_v in data.items()
        }

    if origin is not None:
        raise FormConfigTypeResolutionError(f'Unsupported origin {origin!r} for alias {alias!r}.')

    # Origin is None if the alias is "simple".
    if origin is None:
        # Allow primitive types to live peacefully without an Optional (without needing to create a
        # useless data abstraction).
        if alias is dict:
            return ConfigUntypedDict.from_defaults(data=data, alias=ConfigUntypedDict)

        if alias in PrimitiveArgs:
            # if isinstance(data, dict) and (key := type_key_class(alias)) in data:
            #     return data.get(key)
            if isinstance(data, dict):
                raise FormConfigError(f'Primitive values must be passed directly, not wrapped in dicts (got {data!r}).')
            return data

        if isinstance(alias, type) and issubclass(alias, BaseConfigurableData):
            # Ensuring FormConfigError
            try:
                return alias.from_defaults(data=data, alias=alias)
            except FormConfigError:
                raise
            except Exception as e:
                raise FormConfigError(f'Failed to parse {display_class_name(alias)} from {type(data)!r}.') from e

        else:
            raise FormConfigTypeResolutionError(f'Unsupported alias {alias!r} for data of type {type(data)!r}.')

    return data
