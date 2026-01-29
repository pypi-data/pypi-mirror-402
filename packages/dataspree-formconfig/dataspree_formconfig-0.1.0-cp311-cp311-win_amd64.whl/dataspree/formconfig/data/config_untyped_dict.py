"""Untyped JSON object payload."""

from __future__ import annotations

from typing import Any, Type
from typing_extensions import Self

from dataspree.formconfig.data.base_configurable import BaseConfigurableData, WrapperAlias
from dataspree.formconfig.data.serialize import instantiate_field
from dataspree.formconfig.core.exceptions import FormConfigMetadataError, FormConfigValidationError
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.fields.base_fields import BaseField, FieldJsonText
from dataspree.formconfig.typing.type_utils import type_key_class


class ConfigUntypedDict(dict[str, Any], BaseConfigurableData):
    """Untyped JSON object payload.

    This is a leaf type: it is not recursively parsed/validated beyond being a dict.
    """

    @classmethod
    def build_field_for_type(
        cls: Type[ConfigUntypedDict],
        value: ConfigUntypedDict | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldJsonText | BaseField:
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

        if value is not None:
            metadata['default'] = dict(value)

        return instantiate_field(FieldJsonText, name, metadata)

    def build_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for representation in UI."""
        return dict(self)

    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> Self:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        if isinstance(data, cls):
            return data
        if data is None:
            raise FormConfigValidationError(f'Expected dict for {display_class_name(cls)}, got None.')
        if not isinstance(data, dict):
            raise FormConfigValidationError(f'Expected dict for {display_class_name(cls)}, got {type(data)!r}.')
        return cls(data)
