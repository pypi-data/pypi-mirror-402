from dataspree.formconfig.data.base_configurable import WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldEnum
from enum import Enum
from typing import Any, TypeVar
from typing_extensions import Self

E = TypeVar('E', bound='ConfigEnum')

class ConfigEnum(Enum):
    """Enum content with selectable string values."""
    @classmethod
    def build_field_for_type(cls, value: Self | str | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldEnum | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
    def build_defaults(self) -> str:
        """Create the default value."""
    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> Self:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
