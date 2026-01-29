"""General serialization functionality that can deal with primitive types and BaseConfigurables."""

from __future__ import annotations

from enum import Enum
from types import UnionType
from typing import Any, TypeVar, Union, get_origin, get_args, cast, Type
from pydantic import ValidationError

from dataspree.formconfig.data.base import PrimitiveClass
from dataspree.formconfig.data.base_configurable import BaseConfigurableData, AliasContainerType, WrapperAlias
from dataspree.formconfig.core.exceptions import FormConfigError, FormConfigTypeResolutionError, FormConfigSchemaError
from dataspree.formconfig.fields.base_fields import (
    BaseField,
    FieldString,
    FieldInteger,
    FieldFloat,
    FieldBool,
    FieldJsonText,
    FieldEnum,
)


C = TypeVar('C', bound='BaseConfigurableData')


def build_field(
    name: str,
    value_type: Type[BaseConfigurableData] | PrimitiveClass | AliasContainerType | UnionType | None = None,
    metadata: dict[str, Any] | None = None,
) -> BaseField:
    """Fallback: build a field for a particular value.

    Args:
        value_type: Optional wrapper type for configurable data.
        name: Name of the field.
        metadata: Field metadata, including display name and description.

    Returns:
        BaseField: The suitable UI representation.
    """
    metadata = dict(metadata or {})

    value = metadata.get('default', None)

    if value_type is None:
        value_type = type(value)  # loses generics!

    if value_type is None or value_type is type(None):
        raise FormConfigError(f'Field {name!r} needs a type annotation because default is None.')
        # raise FormConfigError(f'Cannot build field {name!r} without a concrete type.')

    type_without_generics = get_origin(value_type) or value_type

    # Reject typing.Union / X | Y / Optional[X] at field build time.
    if type_without_generics in (Union, UnionType):
        args = get_args(value_type)
        is_optional = any(a is type(None) for a in args)
        if is_optional:
            raise FormConfigTypeResolutionError(
                f'{name!r} is annotated as Optional/None-union ({value_type!r}). Use ConfigOptional[...] instead.'
            )
        raise FormConfigTypeResolutionError(
            f'{name!r} is annotated as a Union ({value_type!r}). Use ConfigUnion[...] instead.'
        )

    if not isinstance(type_without_generics, type):
        raise FormConfigSchemaError(
            f'Unsupported field type {type_without_generics!r} for field {name!r}. '
            'If this is Annotated or a custom typing construct, strip it before calling _build_field.'
        )

    if issubclass(type_without_generics, BaseConfigurableData):
        metadata.pop('default', None)
        return type_without_generics.build_field_for_type(
            value=value,
            name=name,
            metadata=metadata,
            type_specification=cast(WrapperAlias, value_type),
        )

    (md := dict(metadata)).pop('name', None)
    if issubclass(type_without_generics, Enum):
        if value is not None and not isinstance(value, Enum):
            raise FormConfigError(f'Field {name!r} expects enum.Enum default, got {type(value)!r}.')

        md['options'] = [{'text': k.name, 'value': k.value} for k in type_without_generics]
        if value is not None:
            md['default'] = value.value
        elif len(type_without_generics):
            # No implicit default here; allow None unless explicitly provided.
            md.pop('default', None)
            # md['default'] = next(iter(type_without_generics)).value

        return instantiate_field(FieldEnum, name, md)

    if issubclass(type_without_generics, bool):
        if value is not None and not isinstance(value, bool):
            raise FormConfigError(f'Field {name!r} expects bool default, got {type(value)!r}.')
        return instantiate_field(FieldBool, name, md)

    if issubclass(type_without_generics, int):
        if value is not None and not isinstance(value, int):
            raise FormConfigError(f'Field {name!r} expects int default, got {type(value)!r}.')
        return instantiate_field(FieldInteger, name, md)

    if issubclass(type_without_generics, float):
        if value is not None and not isinstance(value, float):
            raise FormConfigError(f'Field {name!r} expects float default, got {type(value)!r}.')
        return instantiate_field(FieldFloat, name, md)

    if issubclass(type_without_generics, dict):
        if value is not None and not isinstance(value, dict):
            raise FormConfigError(f'Field {name!r} expects dict default, got {type(value)!r}.')
        # @dev: both Typed dict[K, V] and untyped dict is currently rendered as JSON text in the UI.
        return instantiate_field(FieldJsonText, name, md)

    if issubclass(type_without_generics, str):
        if value is not None and not isinstance(value, str):
            raise FormConfigError(f'Field {name!r} expects str default, got {type(value)!r}.')
        return instantiate_field(FieldString, name, md)

    raise FormConfigError(f'Unsupported field type {type_without_generics!r} for field {name!r}.')


B = TypeVar('B', bound=BaseField)


def instantiate_field(default_input: Type[B] | None, name: str, metadata: dict[str, Any]) -> B | BaseField:
    """Used to instantiate UI fields."""
    metadata = dict(metadata or {})
    if not isinstance(field := metadata.pop('input', default_input), type) or not issubclass(field, BaseField):
        raise FormConfigError(
            'BaseField has to be specified either as default_input (fallback) or via the metadata as BaseField '
            'subclass.'
        )

    if 'name' in metadata and (md_name := metadata.pop('name')) != name:
        raise FormConfigError(
            f'Ambiguous name provided. Provided name={name} as argument and name = {md_name} in the metadata.'
        )

    # Always remove default if None
    if metadata.get('default') is None:
        metadata.pop('default', None)

    display_name = metadata.pop('display_name', BaseField.capitalize(name))
    try:
        return field(name=name, display_name=display_name, **metadata)
    except (TypeError, ValidationError) as e:
        keys = ', '.join(map(str, metadata.keys()))
        field_name = getattr(field, '__name__', repr(field))
        raise FormConfigError(f'Invalid metadata for field {field_name}: keys=[{keys}]. {e}') from e
