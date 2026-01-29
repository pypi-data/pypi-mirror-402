"""Class containing optional data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Generic, get_origin, Any, Type

from dataspree.formconfig.data.base_configurable import (
    ConfigValue,
    BaseConfigurableData,
    ConfigType,
    WrapperAlias,
    require_valid_config_type,
    build_defaults,
)
from dataspree.formconfig.data.parse import from_defaults
from dataspree.formconfig.data.serialize import build_field, instantiate_field
from dataspree.formconfig.core.exceptions import (
    FormConfigError,
    FormConfigMetadataError,
    FormConfigTypeResolutionError,
    FormConfigParseError,
    FormConfigValidationError,
)
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.fields.base_fields import BaseField, FieldOptional
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from dataspree.formconfig.typing.type_utils import resolve_generic_arg, type_key_class

T = TypeVar('T', bound=ConfigValue)


@dataclass
class ConfigOptional(GenericWithArgs, Generic[T], BaseConfigurableData):
    """Class containing optional data. The argument needs to be of type BaseConfigurableData or a Primitive type.

    Example allowed:
        - ConfigOptional[int]
        - ConfigOptional[ConfigUnion[int | CF]] where CF is of type ConfigData

    Example disallowed:
         - ConfigOptional[int | str]
         - ConfigOptional[list[int]]
         - ConfigOptional
         - ConfigOptional[A] where A is neither of type BaseConfigurableData nor a PrimitiveType
         - ConfigOptional (without parameters). This cannot be checked at annotation time, but at instantiation.
    """

    content: T | None = None  # runtime value (None or T)

    @classmethod
    def _contained_type(cls, alias: WrapperAlias) -> ConfigType:
        """Simple utility function that checks the contained type and returns it.

        Given ConfigOptional[A] this returns A and checks before that A is of type ConfigType.
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
        cls: Type[ConfigOptional[T]],
        value: ConfigOptional[T] | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldOptional | BaseField:
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

        inner_type: ConfigType = cls._contained_type(type_specification)

        content: ConfigValue | None = value.content if isinstance(value, ConfigOptional) else None
        enabled = content is not None

        if (raw_inner_meta := metadata.get('content', {})) is None:
            raw_inner_meta = {}

        if not isinstance(raw_inner_meta, dict):
            raise FormConfigMetadataError(
                f'Field metadata for {display_class_name(cls)}.content must be a dict, got {type(raw_inner_meta)!r}.'
            )

        if 'default' in raw_inner_meta:
            raise FormConfigMetadataError('Ambiguous (inner) default value.')

        inner_meta = dict(raw_inner_meta)
        if enabled:  # only set default if enabled, don't pass None.
            inner_meta['default'] = content

        if 'display_name' not in inner_meta:
            inner_meta['display_name'] = ''

        children = [build_field(value_type=inner_type, name='content', metadata=inner_meta)]

        # Build outer level
        metadata['fields'] = children
        metadata['default'] = enabled

        metadata.pop('content', None)
        return instantiate_field(FieldOptional, name, metadata)

    def build_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for representation in UI."""
        if self.content is None:
            return {'default': False}

        # if isinstance(self.content, BaseConfigurableData):
        #    return {'default': True, **self.content.build_defaults()}
        return {'default': True, 'content': build_defaults(self.content)}

        # return {'default': True, type_key_class(type(self.content)): self.content}

    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> ConfigOptional[T]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        if alias is None:
            alias = cls

        # Guard: check that there are type arguments
        if (inner_alias := resolve_generic_arg(alias, default=None)) is None:
            raise FormConfigTypeResolutionError(f'{display_class_name(cls)} must be parametrised.')

        if isinstance(inner_alias, TypeVar):
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} must be parametrised (not with a TypeVar {display_class_name(alias)}).'
            )

        # Check the input type
        if not isinstance(data, dict):
            raise FormConfigParseError(f'Expected dict data for {display_class_name(cls)}, got {type(data)!r}.')

        # Basically expressive version of
        # if not (enabled := bool(data.get('default'))) != (content is None):  # @dev: treating no default as disabled.
        #    raise FormConfigError(f'{display_class_name(cls)} has enabled={enabled} but "content"={content}.')

        enabled: bool = bool(data.get('default'))
        has_content: bool = (content := data.get('content')) is not None

        if enabled and not has_content:
            raise FormConfigValidationError(f'{display_class_name(cls)} is enabled but "content" is missing or None.')

        if not enabled and has_content:
            raise FormConfigValidationError(f'{display_class_name(cls)} is disabled but "content" is present.')

        if not enabled:
            return cls(None)

        return cls(from_defaults(data=content, alias=inner_alias))

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
