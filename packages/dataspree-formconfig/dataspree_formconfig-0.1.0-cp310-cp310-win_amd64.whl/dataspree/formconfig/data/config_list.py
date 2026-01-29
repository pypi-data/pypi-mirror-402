"""List content of repeated items (e.g., dataclasses or other wrappers)."""

from __future__ import annotations

from typing import TypeVar, get_origin, Any, Type

from dataspree.formconfig.data.base_configurable import (
    ConfigValue,
    BaseConfigurableData,
    WrapperAlias,
    ConfigType,
    require_valid_config_type,
    build_defaults,
)
from dataspree.formconfig.data.parse import from_defaults
from dataspree.formconfig.data.serialize import instantiate_field, build_field
from dataspree.formconfig.core.exceptions import (
    FormConfigError,
    FormConfigTypeResolutionError,
    FormConfigMetadataError,
    FormConfigParseError,
)
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.fields.base_fields import BaseField, FieldList
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from dataspree.formconfig.typing.type_utils import resolve_generic_arg, type_key_class

T = TypeVar('T', bound=ConfigValue)


class ConfigList(GenericWithArgs, list[T], BaseConfigurableData):
    """List content of repeated items (e.g., dataclasses or other wrappers).

    Example allowed:
        - ConfigList[int]
        - ConfigList[ConfigUnion[int | CF]] where CF is of type ConfigData

    Example disallowed:
         - ConfigList[int | str]
         - ConfigList[list[int]]
         - ConfigList
         - ConfigList[A] where A is neither of type BaseConfigurableData nor a PrimitiveType
         - ConfigList (without parameters). This cannot be checked at annotation time, but at instantiation.
    """

    @classmethod
    def _contained_type(cls, alias: WrapperAlias) -> ConfigType:
        """Simple utility function that checks the contained type and returns it.

        Given ConfigList[A] this returns A and checks before that A is of type ConfigType.
        """
        origin = get_origin(alias) or alias
        origin_cls = getattr(cls, '__origin__', None)
        if not isinstance(origin_cls, type):
            origin_cls = cls

        if not isinstance(origin, type) or not issubclass(origin, origin_cls):
            raise FormConfigTypeResolutionError(f'Alias must be a {display_class_name(cls)}.')

        if (child_arg := resolve_generic_arg(alias, of=origin_cls, index=0, default=None)) is None:
            raise FormConfigTypeResolutionError(f'{display_class_name(cls)} must be parametrised.')

        try:
            return require_valid_config_type(child_arg)
        except FormConfigError as e:
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} parameter must be PrimitiveType or BaseConfigurableData: {e}'
            )

    @classmethod
    def build_field_for_type(
        cls: Type[ConfigList[T]],
        value: ConfigList[T] | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldList | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
        metadata = dict(metadata or {})
        if 'default' in metadata:
            raise FormConfigMetadataError('Ambiguous default value.')

        name = name or type_key_class(cls)
        if type_specification is None:
            type_specification = cls.typing_alias()

        # Build the child. value is None here, because the child does
        inner_type = cls._contained_type(type_specification)
        # We could also attempt `value = value[-1] if value else None`; then the default for a new list item is the
        # last item that existed before. But probably this is supposed to be something that the UI defines.
        # Make sure that the default value is None

        if (raw_inner := metadata.pop('content', {})) is None:
            raw_inner = {}

        if not isinstance(raw_inner, dict):
            raise FormConfigMetadataError(
                f'Field metadata for {display_class_name(cls)}.content must be a dict, got {type(raw_inner)!r}.'
            )

        (inner_metadata := dict(raw_inner)).pop('default', None)
        if 'display_name' not in inner_metadata:
            inner_metadata['display_name'] = ''

        proto_field = build_field(value_type=inner_type, name='content', metadata=inner_metadata)

        # Build outer level
        metadata['fields'] = [proto_field]
        metadata['default'] = value.build_defaults() if isinstance(value, ConfigList) else []
        return instantiate_field(FieldList, name, metadata)

    def build_defaults(self) -> list[Any]:
        """Emit list items as row objects under 'content'."""
        return [{'content': build_defaults(x)} for x in self]

    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any | None, alias: WrapperAlias | None = None) -> ConfigList[T]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        rows: list[Any]
        if data is None:
            rows = []
        elif isinstance(data, list):
            rows = data
        else:
            raise FormConfigParseError(f'Expected list data for {display_class_name(cls)}, got {type(data)!r}.')

        if alias is None:
            alias = cls

        # Guard: check that there are type arguments
        # @dev We want to use resolve_generic_arg here, because we want to use alias.
        origin_cls = cls.__origin__ or cls
        if (inner_alias := resolve_generic_arg(alias, of=origin_cls, default=None)) is None:
            raise FormConfigTypeResolutionError(f'{display_class_name(cls)} must be parametrised.')

        items = []
        for row in rows:
            inner_data = row['content'] if isinstance(row, dict) and set(row.keys()) == {'content'} else row
            items.append(from_defaults(data=inner_data, alias=inner_alias))
        return cls(items)

    def __class_getitem__(cls, item: Any) -> Any:
        """Validate generic argument at alias creation time.

        This explicitly disallows Annotated for now.
        """
        o = get_origin(item) or item

        try:
            require_valid_config_type(o)
        except FormConfigError as e:
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} cannot contain non configurable types {item!r} {e}.'
            )

        return super().__class_getitem__(item)
