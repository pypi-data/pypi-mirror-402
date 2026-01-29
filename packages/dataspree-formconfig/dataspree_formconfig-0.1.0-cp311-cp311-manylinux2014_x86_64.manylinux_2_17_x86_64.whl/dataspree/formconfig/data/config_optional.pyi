from dataclasses import dataclass
from dataspree.formconfig.data.base_configurable import BaseConfigurableData, ConfigType as ConfigType, ConfigValue, WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldOptional
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from typing import Any, Generic, TypeVar

T = TypeVar('T', bound=ConfigValue)

@dataclass
class ConfigOptional(GenericWithArgs, BaseConfigurableData, Generic[T]):
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
    content: T | None = ...
    @classmethod
    def build_field_for_type(cls, value: ConfigOptional[T] | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldOptional | BaseField:
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
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> ConfigOptional[T]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
    def __class_getitem__(cls, item: Any) -> Any:
        """Validate generic argument at alias creation time.

        This explicitly disallows Annotated for now.
        """
