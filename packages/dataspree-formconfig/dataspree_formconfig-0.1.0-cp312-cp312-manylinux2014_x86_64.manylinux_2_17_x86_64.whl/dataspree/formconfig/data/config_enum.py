"""Enum content with selectable string values."""

from __future__ import annotations

from typing import TypeVar, cast, Any, Type
from typing_extensions import Self
from enum import Enum


from dataspree.formconfig.data.base_configurable import BaseConfigurableData, build_defaults, WrapperAlias
from dataspree.formconfig.data.serialize import instantiate_field
from dataspree.formconfig.core.exceptions import FormConfigError, FormConfigMetadataError
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.fields.base_fields import BaseField, FieldEnum
from dataspree.formconfig.typing.type_utils import type_key_class


E = TypeVar('E', bound='ConfigEnum')


class ConfigEnum(Enum):
    """Enum content with selectable string values."""

    @classmethod
    def build_field_for_type(
        cls: Type[Self],
        value: Self | str | None = None,
        type_specification: WrapperAlias | None = None,  # noqa
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldEnum | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
        parsed: Self | None
        if isinstance(value, str):
            parsed = cls.from_defaults(value)
        else:
            parsed = value

        metadata = dict(metadata or {})
        if 'default' in metadata:
            raise FormConfigMetadataError('Ambiguous default value.')

        name = name or type_key_class(cls)
        metadata['options'] = [{'text': e.name, 'value': e.value} for e in cast(Any, cls)]

        # Intentionally keep the default value None if value is None. The front-end / front-end facing code
        # (i.e., FieldEnum) can decide if a value should be supplied in spite of that.
        if parsed is not None and (default_value := build_defaults(parsed)) is not None:
            metadata['default'] = default_value  # noqa

        return instantiate_field(FieldEnum, name, metadata)

    def build_defaults(self) -> str:
        """Create the default value."""
        return cast(str, cast(object, self.value))

    @classmethod
    def from_defaults(
        cls,
        data: dict[str, Any] | Any,
        alias: WrapperAlias | None = None,  # noqa
    ) -> Self:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            data = data.get('value', data.get('default', data))
        try:
            # by value
            return cls(data)
        except (ValueError, TypeError):
            if isinstance(data, str):
                try:
                    # by name
                    return cast(Self, cast(Any, cls)[data])
                except KeyError:
                    pass

        raise FormConfigError(f'Invalid {display_class_name(cls)}: {data!r}')


BaseConfigurableData.register(ConfigEnum)
