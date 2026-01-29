from dataspree.formconfig.data.base_configurable import BaseConfigurableData, WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldJsonText
from typing import Any
from typing_extensions import Self

class ConfigUntypedDict(dict[str, Any], BaseConfigurableData):
    """Untyped JSON object payload.

    This is a leaf type: it is not recursively parsed/validated beyond being a dict.
    """
    @classmethod
    def build_field_for_type(cls, value: ConfigUntypedDict | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldJsonText | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
    def build_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for representation in UI."""
    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> Self:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
