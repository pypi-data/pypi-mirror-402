from dataspree.formconfig.data.base_configurable import BaseConfigurableData, ConfigType as ConfigType, ConfigValue, WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldList
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from typing import Any, TypeVar

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
    def build_field_for_type(cls, value: ConfigList[T] | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldList | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
    def build_defaults(self) -> list[Any]:
        """Emit list items as row objects under 'content'."""
    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any | None, alias: WrapperAlias | None = None) -> ConfigList[T]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
    def __class_getitem__(cls, item: Any) -> Any:
        """Validate generic argument at alias creation time.

        This explicitly disallows Annotated for now.
        """
