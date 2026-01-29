from dataclasses import dataclass
from dataspree.formconfig.data.base_configurable import BaseConfigurableData, WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldData
from typing import Any

@dataclass
class ConfigData(BaseConfigurableData):
    """Nested dataclass content for grouped input fields."""
    @classmethod
    def build_field_for_type(cls, value: ConfigData | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldData | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
    @classmethod
    def from_defaults(cls, data: dict[str, Any] | None | Any, alias: WrapperAlias | None = None) -> ConfigData:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
