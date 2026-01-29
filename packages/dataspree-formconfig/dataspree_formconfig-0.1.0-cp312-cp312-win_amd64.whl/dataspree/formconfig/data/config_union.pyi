from dataclasses import dataclass
from dataspree.formconfig.data.base_configurable import BaseConfigurableData, ConfigValue, WrapperAlias as WrapperAlias
from dataspree.formconfig.fields.base_fields import BaseField as BaseField, FieldUnion
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from typing import Any, Generic, TypeVar

U = TypeVar('U', bound=ConfigValue)

@dataclass
class ConfigUnion(GenericWithArgs, BaseConfigurableData, Generic[U]):
    """Templated union of multiple types selectable via UI.

    Allowed:
    - ConfigUnion[A | B | ...] where A, B, ... are of type BaseConfigurableData or PrimitiveTypes.
    - ConfigUnion[Union[A, ...]] where A, ... are of type BaseConfigurableData or PrimitiveTypes.

    Example allowed:
        - ConfigUnion[Union[A, int]]
        - ConfigUnion[Union[int]]
        - ConfigUnion[int | A]

    Example disallowed:
         - ConfigUnion[int | type(None)]
         - ConfigUnion[X | A] where X is neither of type BaseConfigurableData or PrimitiveTypes
         - ConfigUnion[Union[X, A]] where X is neither of type BaseConfigurableData or PrimitiveTypes
         - ConfigUnion (without parameters). This cannot be checked at annotation time, but at instantiation
         - ConfigUnion[A] where A is arbitrary (can be BaseConfigurableData or PrimitiveTypes).
    """
    content: ConfigValue | None = ...
    @property
    def selected(self) -> str | None:
        """Return the identifier of the current selection."""
    @classmethod
    def build_field_for_type(cls, value: ConfigUnion[U] | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> FieldUnion | BaseField:
        """Transform an instance of this class or None into the representation of this class."""
    def build_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for representation in UI."""
    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> ConfigUnion[U]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
    def __class_getitem__(cls, item: Any) -> Any:
        """Validate generic argument at alias creation time.

        This explicitly disallows Annotated for now.
        """
